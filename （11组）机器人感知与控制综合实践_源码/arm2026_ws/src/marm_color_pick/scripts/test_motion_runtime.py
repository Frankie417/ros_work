#!/usr/bin/env python3
"""Exercise the virtual teaching interfaces; never connects to real actuators."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import rospy
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from pick_core import Arm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(rospy.myargv()[1:])
    rospy.init_node('motion_interface_check', anonymous=True)
    latest = {}
    received = [0]
    def receive(msg):
        latest.clear()
        latest.update(json.loads(msg.data))
        received[0] += 1
    subscriber = rospy.Subscriber('/color_pick/status', String, receive)
    joints = rospy.Publisher('/color_pick/joint_target', JointState, queue_size=1)
    points = rospy.Publisher('/color_pick/target', PointStamped, queue_size=1)
    reset = rospy.ServiceProxy('/color_pick/reset', Trigger)
    def wait(predicate, seconds=8):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline and not rospy.is_shutdown():
            if predicate():
                return
            rospy.sleep(.03)
        raise AssertionError('Motion interface timed out: '+str(latest.get('state')))
    wait(lambda: latest and joints.get_num_connections() and points.get_num_connections())
    assert latest['mode'] == 'kinematic_virtual_camera' and not latest['active'] and not latest['queue']
    before_reset = received[0]
    assert reset().success
    wait(lambda: received[0] >= before_reset+2 and latest['state'] == '等待任务' and not latest['completed'])
    arm = Arm(rospy.get_param('/robot_description'), rospy.get_param('/color_pick/cube_size'))
    checks = []
    def move(names, values, label, check_busy=False):
        expected = np.array(latest['joints'])
        for n, v in zip(names, values):
            expected[arm.names.index(n)] = v
        joints.publish(JointState(name=names, position=values))
        wait(lambda: latest.get('active') == 'manual')
        if check_busy:
            assert not reset().success, 'Busy reset accepted'
        wait(lambda: latest.get('active') is None)
        assert np.max(np.abs(np.array(latest['joints'])-expected)) < 1e-5
        checks.append(label)
    q = latest['joints'][:]
    move([arm.names[0]], [q[0]+.12], 'single_joint', True)
    move([arm.names[0], arm.names[5]], [q[0]-.08, q[5]+.10], 'coordinated_joints')
    move([arm.names[-1]], [arm.grip], 'gripper_close')
    move([arm.names[-1]], [arm.open], 'gripper_open')
    before = np.array(latest['joints'])
    joints.publish(JointState(name=[arm.names[0]], position=[99.]))
    rospy.sleep(.3)
    assert np.max(np.abs(np.array(latest['joints'])-before)) < 1e-9 and latest['active'] is None
    checks.append('out_of_limit_rejected')
    joints.publish(JointState(name=[arm.names[0], arm.names[0]], position=[0., 0.]))
    rospy.sleep(.3)
    assert np.max(np.abs(np.array(latest['joints'])-before)) < 1e-9
    checks.append('duplicate_joint_rejected')
    assert reset().success
    rospy.sleep(.3)
    goal = PointStamped()
    goal.header.frame_id = 'wrong_frame'
    goal.point.x, goal.point.y, goal.point.z = .24, .02, .15
    before = np.array(latest['joints'])
    points.publish(goal)
    rospy.sleep(.3)
    assert np.max(np.abs(np.array(latest['joints'])-before)) < 1e-9
    checks.append('wrong_frame_rejected')
    goal.header.frame_id = 'marm_mod_base_link'
    points.publish(goal)
    wait(lambda: latest.get('active') == 'manual')
    wait(lambda: latest.get('active') is None)
    position = arm.object_pose(latest['joints'])[0]
    error = float(np.linalg.norm(position-[.24, .02, .15]))
    assert error < 1e-7
    checks.append('cartesian_point_to_point')
    before = np.array(latest['joints'])
    goal.point.x = 3.
    points.publish(goal)
    rospy.sleep(.3)
    assert np.max(np.abs(np.array(latest['joints'])-before)) < 1e-9
    checks.append('unreachable_rejected')
    assert reset().success
    record = dict(result='PASS', checks=checks, busy_reset_rejected=True, cartesian_fk_error_m=error,
                  scope='live ROS virtual model only; no physical robot control or full collision checking')
    Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps(record, ensure_ascii=False, indent=2))
    subscriber.unregister()


if __name__ == '__main__':
    main()
