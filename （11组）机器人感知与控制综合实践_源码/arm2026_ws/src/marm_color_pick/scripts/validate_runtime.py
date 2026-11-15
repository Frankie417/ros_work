#!/usr/bin/env python3
"""Reset the virtual scene and verify a complete live four-colour cycle."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import rospy
import tf
from std_msgs.msg import String
from std_srvs.srv import Trigger
from pick_core import Arm, COLORS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(rospy.myargv()[1:])
    rospy.init_node('color_pick_runtime_check', anonymous=True)
    arm = Arm(rospy.get_param('/robot_description'), rospy.get_param('/color_pick/cube_size'))
    tf_listener = tf.TransformListener()
    latest, maximum_height, states = {}, {}, set()
    velocity_max = np.zeros(7)
    previous = [None, None]

    def callback(msg):
        data = json.loads(msg.data)
        latest.clear()
        latest.update(data)
        color = data['attached']
        if color:
            maximum_height[color] = max(maximum_height.get(color, 0), data['blocks'][color][2])
        states.add(data['state'])
        now = time.monotonic()
        if previous[0] is not None and now-previous[0] > .01:
            velocity_max[:] = np.maximum(velocity_max, np.abs(np.array(data['joints'])-previous[1])/(now-previous[0]))
        previous[:] = [now, np.array(data['joints'])]

    subscriber = rospy.Subscriber('/color_pick/status', String, callback)
    rospy.wait_for_service('/color_pick/reset', timeout=10)
    rospy.ServiceProxy('/color_pick/reset', Trigger)()
    deadline = time.monotonic()+10
    while not rospy.is_shutdown() and time.monotonic() < deadline:
        if latest and not latest['active'] and not latest['completed'] and not latest['queue']:
            break
        rospy.sleep(.05)
    else:
        raise RuntimeError('Reset did not finish')
    previous[:] = [None, None]
    velocity_max[:] = 0
    maximum_height.clear()
    publisher = rospy.Publisher('/color_pick/command', String, queue_size=1)
    deadline = time.monotonic()+10
    while publisher.get_num_connections() == 0 and time.monotonic() < deadline:
        rospy.sleep(.05)
    publisher.publish(String('all'))
    deadline = time.monotonic()+90
    while not rospy.is_shutdown() and time.monotonic() < deadline:
        if latest.get('error'):
            raise RuntimeError(latest['error'])
        if len(latest.get('completed', [])) == 4 and latest['active'] is None:
            break
        rospy.sleep(.05)
    else:
        raise RuntimeError('Four-colour cycle timed out')
    assert latest['completed'] == list(COLORS)
    assert len(latest['events']) == 8
    resting_z = rospy.get_param('/color_pick/table_height')+arm.size/2
    assert all(maximum_height[c] > resting_z+.05 for c in COLORS)
    assert max(e['error_m'] for e in latest['events']) < .002
    assert np.all(velocity_max < 3.14), velocity_max
    rospy.sleep(.2)
    translation, rotation = tf_listener.lookupTransform('marm_mod_base_link', 'marm_mod_grasping_frame', rospy.Time(0))
    expected = arm.fk(latest['joints'])['marm_mod_grasping_frame'][:3, 3]
    tf_error = float(np.linalg.norm(np.array(translation)-expected))
    assert tf_error < 1e-7
    record = dict(result='PASS', completed=latest['completed'], events=latest['events'],
                  maximum_attached_height_m=maximum_height, resting_height_m=resting_z,
                  observed_states=sorted(states), maximum_observed_joint_speed_rad_s=velocity_max.tolist(),
                  final_tf_position_error_m=tf_error, final_blocks=latest['blocks'],
                  scope='live ROS kinematic virtual-camera demonstration, not physical grasp validation')
    Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps(record, ensure_ascii=False, indent=2))
    subscriber.unregister()


if __name__ == '__main__':
    main()
