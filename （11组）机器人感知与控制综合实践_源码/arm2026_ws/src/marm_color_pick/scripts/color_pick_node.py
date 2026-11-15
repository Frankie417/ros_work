#!/usr/bin/env python3
"""Kinematic four-colour sorting; no hardware, contact dynamics or MoveIt."""
import json
import math
from pathlib import Path
import sys
import threading
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import rospy
from sensor_msgs.msg import Image, JointState
from geometry_msgs.msg import PointStamped
from std_msgs.msg import String
from std_srvs.srv import Trigger, TriggerResponse
from visualization_msgs.msg import Marker, MarkerArray
from tf.transformations import quaternion_from_matrix
from pick_core import Arm, Camera, COLORS, BGR, CHINESE, transform


class Demo:
    def __init__(self):
        self.config = rospy.get_param('~')
        self.size = self.config['cube_size']
        self.arm = Arm(rospy.get_param('/robot_description'), self.size)
        self.camera = Camera(self.config['camera'])
        self.lock = threading.Lock()
        self.external = self.config.get('external_perception', False)
        self.observations, self.observation_stamp = {}, 0.
        self.raw_pub = rospy.Publisher('/color_pick/image_raw', Image, queue_size=1)
        self.requests, self.reset_requested = [], False
        self.manual = None
        self.joints_pub = rospy.Publisher('/joint_states', JointState, queue_size=1)
        self.markers_pub = rospy.Publisher('/color_pick/markers', MarkerArray, queue_size=1)
        self.image_pub = rospy.Publisher('/color_pick/detection_image', Image, queue_size=1)
        self.status_pub = rospy.Publisher('/color_pick/status', String, queue_size=1, latch=True)
        rospy.Subscriber('/color_pick/command', String, self.command)
        rospy.Subscriber('/color_pick/joint_target', JointState, self.joint_target, queue_size=1)
        rospy.Subscriber('/color_pick/target', PointStamped, self.point_target, queue_size=1)
        if self.external:
            rospy.Subscriber('/color_pick/observations', String, self.observe, queue_size=1)
        rospy.Service('/color_pick/reset', Trigger, self.reset)
        self.reset_scene(self.config.get('auto_start', True))

    def queue_manual(self, target, cartesian=None):
        with self.lock:
            if self.active or self.queue or self.requests or self.manual or self.error or self.reset_requested:
                raise ValueError('Manual motion requires an idle scene without errors')
            if not np.isfinite(target).all() or not np.all((target >= self.arm.limits[:, 0]) & (target <= self.arm.limits[:, 1])):
                raise ValueError('Manual joint target violates URDF limits')
            velocities = np.array([float(self.arm.by_name[n].find('limit').get('velocity')) for n in self.arm.names])
            slopes = np.abs(target-self.q)
            start_point = self.arm.object_pose(self.q)[0]
            if cartesian is not None:
                # Cartesian commands start from a valid downward-grasp posture.
                if np.linalg.norm(self.arm.ik(start_point, self.q[-1])-self.q) > 1e-5:
                    raise ValueError('Cartesian command requires the downward-grasp posture; reset first')
                samples = [self.arm.ik(start_point*(1-u)+cartesian*u, self.q[-1]) for u in np.linspace(0, 1, 101)]
                slopes = np.max(np.abs(np.diff(samples, axis=0)), axis=0)*100
                if min(start_point[2], cartesian[2]) < self.config['table_height']+self.size/2:
                    raise ValueError('Cartesian target is below the reference tabletop height')
            duration = max(self.config['move_duration'], float(np.max(slopes/velocities))*1.5*1.1)
            self.manual = dict(start=self.q.copy(), target=target, point=cartesian,
                               start_point=start_point, started=None, duration=duration)

    def joint_target(self, msg):
        try:
            if not msg.name or len(msg.name) != len(msg.position) or len(set(msg.name)) != len(msg.name):
                raise ValueError('JointState requires unique names with matching positions')
            target = self.q.copy()
            for name, value in zip(msg.name, msg.position):
                if name not in self.arm.names:
                    raise ValueError('Unknown joint name')
                target[self.arm.names.index(name)] = value
            self.queue_manual(target)
        except ValueError as error:
            rospy.logwarn('Joint command rejected: %s', error)

    def point_target(self, msg):
        try:
            if msg.header.frame_id != 'marm_mod_base_link':
                raise ValueError('Target frame must be marm_mod_base_link')
            point = np.array([msg.point.x, msg.point.y, msg.point.z])
            self.queue_manual(self.arm.ik(point, self.q[-1]), point)
        except ValueError as error:
            rospy.logwarn('Point command rejected: %s', error)

    def reset_scene(self, start=False):
        z = self.config['table_height']+self.size/2
        self.blocks = {c: np.array([self.config['source_x'], y, z])
                       for c, y in zip(COLORS, self.config['rows'])}
        self.destinations = {c: np.array([self.config['destination_x'], y, z])
                             for c, y in zip(COLORS, self.config['rows'])}
        # Align each cube's side faces with the radial closing direction.
        # Otherwise a diagonally presented cube would be wider than its nominal side.
        self.rotations = {c: transform(rpy=(0, 0, math.atan2(p[1], p[0])))[:3, :3]
                          for c, p in self.blocks.items()}
        self.completed, self.events = [], []
        self.queue = list(COLORS) if start else []
        self.steps, self.step_index = [], 0
        self.active, self.attached, self.error = None, None, ''
        self.manual = None
        self.q = self.arm.ik(self.arm.home)
        self.state = '等待任务'
        self.last_camera = -1.
        self.detected = {}
        self.observations, self.observation_stamp = {}, 0.

    def observe(self, msg):
        try:
            data = json.loads(msg.data)
            stamp = float(data['stamp'])
            if data.get('calibration') != 'virtual_orthographic_v1' or not 0 <= rospy.get_time()-stamp <= .5:
                return
            points = data['stable']
            for color, point in points.items():
                if color not in COLORS or len(point) != 2 or not np.isfinite(point).all():
                    return
                if not abs(point[0]-self.config['source_x']) <= .03:
                    return
                if not self.config['camera']['y_min'] <= point[1] <= self.config['camera']['y_max']:
                    return
            with self.lock:
                if stamp > self.observation_stamp:
                    self.observations, self.observation_stamp = points, stamp
        except (ValueError, KeyError, TypeError):
            rospy.logwarn_throttle(2, 'Invalid perception result rejected')

    def command(self, msg):
        aliases = {'红': 'red', '黄': 'yellow', '蓝': 'blue', '绿': 'green',
                   '红色': 'red', '黄色': 'yellow', '蓝色': 'blue', '绿色': 'green', '全部': 'all'}
        value = aliases.get(msg.data.strip(), msg.data.strip().lower())
        if value not in COLORS+('all',):
            rospy.logwarn('Unknown colour; use red/yellow/blue/green/all or 红/黄/蓝/绿/全部')
            return
        with self.lock:
            self.requests.append(value)

    def reset(self, _):
        with self.lock:
            if self.active or self.queue or self.requests or self.manual:
                return TriggerResponse(False, 'Reset requires an idle virtual arm')
            self.reset_requested = True
        return TriggerResponse(True, 'Reset queued; virtual scene only')

    def move(self, label, position):
        return dict(kind='move', label=label, position=np.array(position), duration=self.config['move_duration'])

    def start_job(self, color, now):
        if color not in self.detected:
            raise ValueError('Camera did not detect '+color)
        source = np.array(self.detected[color]+[self.config['table_height']+self.size/2])
        target = self.destinations[color]
        lift = np.array([0, 0, self.config['lift_height']])
        self.steps = [self.move('接近方块', source+lift), self.move('下降对准', source),
                      dict(kind='close', label='闭爪抓取', duration=self.config['grip_duration']),
                      self.move('抬起方块', source+lift), self.move('搬运至色区', target+lift),
                      self.move('下降放置', target),
                      dict(kind='open', label='松爪放置', duration=self.config['grip_duration']),
                      self.move('抬爪撤离', target+lift)]
        # Validate the entire Cartesian path before changing the first joint.
        point, _ = self.arm.object_pose(self.q)
        for step in self.steps:
            if step['kind'] == 'move':
                samples = []
                for u in np.linspace(0, 1, 41):
                    samples.append(self.arm.ik(point*(1-u)+step['position']*u))
                slopes = np.max(np.abs(np.diff(samples, axis=0)), axis=0)*40
                velocities = np.array([float(self.arm.by_name[n].find('limit').get('velocity')) for n in self.arm.names])
                step['duration'] = max(step['duration'], float(np.max(slopes/velocities))*1.5*1.1)
                point = step['position']
        self.active, self.step_index = color, 0
        self.begin_step(now)
        rospy.loginfo('开始%s方块任务：HSV定位=(%.4f, %.4f)', CHINESE[color], source[0], source[1])

    def begin_step(self, now):
        self.step_start = now
        self.start_position = self.arm.object_pose(self.q)[0]
        self.start_grip = self.q[-1]
        self.state = self.steps[self.step_index]['label']

    def finish_step(self, step):
        if step['kind'] == 'close':
            position, _ = self.arm.object_pose(self.q)
            error = float(np.linalg.norm(position-self.blocks[self.active]))
            if error > .002 or abs(self.q[-1]-self.arm.grip) > 1e-5:
                raise ValueError('Grasp gate failed; no attachment: error=%g' % error)
            frame = self.arm.fk(self.q)['marm_mod_gripper_stator']
            world = np.eye(4)
            world[:3, 3] = self.blocks[self.active]
            world[:3, :3] = self.rotations[self.active]
            self.attachment = np.linalg.inv(frame) @ world
            self.attached = self.active
            self.events.append(dict(event='attach', color=self.active, error_m=error))
        elif step['kind'] == 'open':
            error = float(np.linalg.norm(self.blocks[self.active]-self.destinations[self.active]))
            if error > .002:
                raise ValueError('Release gate failed; target error=%g' % error)
            self.attached = None
            self.completed.append(self.active)
            self.events.append(dict(event='place', color=self.active, error_m=error))
            rospy.loginfo('%s方块放置完成，误差%.6f m (%d/4)', CHINESE[self.active], error, len(self.completed))

    def tick(self, now):
        with self.lock:
            requests, reset = self.requests, self.reset_requested
            self.requests, self.reset_requested = [], False
        if reset:
            self.reset_scene(False)
        for value in requests:
            for color in (COLORS if value == 'all' else (value,)):
                if color not in self.queue and color not in self.completed and color != self.active:
                    self.queue.append(color)
        if now-self.last_camera > .1:
            visible = {c: p for c, p in self.blocks.items() if c != self.attached}
            raw = self.camera.render(visible, self.size, self.rotations)
            self.detected, debug = self.camera.detect(raw) if not self.external else ({}, raw)
            msg = Image()
            msg.header.stamp = rospy.Time.now()
            msg.header.frame_id = 'virtual_overhead_camera'
            msg.height, msg.width = debug.shape[:2]
            msg.encoding, msg.step, msg.data = 'bgr8', debug.shape[1]*3, debug.tobytes()
            self.image_pub.publish(msg)
            msg.data = raw.tobytes()
            self.raw_pub.publish(msg)
            self.last_camera = now
        if self.external:
            with self.lock:
                self.detected = dict(self.observations) if 0 <= now-self.observation_stamp <= .5 else {}
        if not self.error:
            try:
                if self.manual:
                    motion = self.manual
                    if motion['started'] is None:
                        motion['started'] = now
                    u = min(1., max(0., (now-motion['started'])/motion['duration']))
                    blend = u*u*(3-2*u)
                    if motion['point'] is None:
                        self.q = motion['start']*(1-blend)+motion['target']*blend
                        self.state = '关节示教运动'
                    else:
                        self.q = self.arm.ik(motion['start_point']*(1-blend)+motion['point']*blend, self.q[-1])
                        self.state = '末端点到点运动'
                    if u >= 1:
                        with self.lock:
                            self.manual = None
                        self.state = '等待任务'
                if self.active is None and not self.manual and self.queue:
                    if not self.external or self.queue[0] in self.detected:
                        self.start_job(self.queue.pop(0), now)
                    else:
                        self.state = '等待稳定视觉目标'
                if self.active is not None:
                    step = self.steps[self.step_index]
                    u = min(1., max(0., (now-self.step_start)/step['duration']))
                    blend = u*u*(3-2*u)
                    if step['kind'] == 'move':
                        position = self.start_position*(1-blend)+step['position']*blend
                        self.q = self.arm.ik(position, self.q[-1])
                    else:
                        end = self.arm.grip if step['kind'] == 'close' else self.arm.open
                        self.q[-1] = self.start_grip*(1-blend)+end*blend
                    if self.attached:
                        world = self.arm.fk(self.q)['marm_mod_gripper_stator'] @ self.attachment
                        self.blocks[self.attached] = world[:3, 3].copy()
                        self.rotations[self.attached] = world[:3, :3].copy()
                    if u >= 1:
                        self.finish_step(step)
                        self.step_index += 1
                        if self.step_index == len(self.steps):
                            self.active = None
                            self.state = '四色完成' if len(self.completed) == 4 else '等待任务'
                        else:
                            self.begin_step(now)
            except ValueError as error:
                self.error, self.state = str(error), '任务停止：验证失败'
                self.queue = []
                rospy.logerr('%s', self.error)
        self.publish()

    def marker(self, ident, kind, xyz, scale, rgba, text='', rotation=None):
        m = Marker()
        m.header.frame_id = 'marm_mod_base_link'
        m.header.stamp = rospy.Time.now()
        m.ns, m.id, m.type, m.action = 'color_pick', ident, kind, Marker.ADD
        m.pose.position.x, m.pose.position.y, m.pose.position.z = map(float, xyz)
        q = [0, 0, 0, 1]
        if rotation is not None:
            matrix = np.eye(4)
            matrix[:3, :3] = rotation
            q = quaternion_from_matrix(matrix)
        m.pose.orientation.x, m.pose.orientation.y, m.pose.orientation.z, m.pose.orientation.w = map(float, q)
        m.scale.x, m.scale.y, m.scale.z = scale
        m.color.r, m.color.g, m.color.b, m.color.a = rgba
        m.text = text
        return m

    def publish(self):
        msg = JointState()
        msg.header.stamp = rospy.Time.now()
        msg.name, msg.position = self.arm.names, self.q.tolist()
        self.joints_pub.publish(msg)
        markers = [self.marker(0, Marker.CUBE, [.245, 0, .045], [.29, .42, .03], [.18, .21, .25, 1])]
        for i, color in enumerate(COLORS):
            rgb = tuple(v/255 for v in BGR[color][::-1])
            target = self.destinations[color].copy()
            target[2] = self.config['table_height']+.0005
            markers.append(self.marker(10+i, Marker.CUBE, self.blocks[color], [self.size]*3,
                                       rgb+(1.,), rotation=self.rotations[color]))
            markers.append(self.marker(20+i, Marker.CUBE, target, [.052, .052, .001], rgb+(.5,)))
            target[2] += .005
            target[0] -= .048
            markers.append(self.marker(30+i, Marker.TEXT_VIEW_FACING, target, [0, 0, .015],
                                       rgb+(1.,), color.upper()))
        # RViz's bundled font is not reliably CJK-capable. Chinese status is on ROS topic/logs.
        label = ('KINEMATIC COLOUR SORTING | %d / 4' % len(self.completed))
        if self.active:
            label += ' | '+self.active.upper()
        if self.error:
            label = 'STOPPED: '+self.error
        markers.append(self.marker(50, Marker.TEXT_VIEW_FACING, [.22, 0, .55], [0, 0, .020], [.9, .95, 1, 1], label))
        self.markers_pub.publish(MarkerArray(markers))
        status = dict(mode='kinematic_virtual_camera', state=self.state, active='manual' if self.manual else self.active,
                      attached=self.attached, completed=self.completed, queue=self.queue, error=self.error,
                      detected=self.detected, joints=self.q.tolist(), events=self.events,
                      perception_source='ros_image_topic' if self.external else 'embedded_virtual_camera',
                      perception_fresh=bool(self.detected),
                      blocks={c: p.tolist() for c, p in self.blocks.items()})
        self.status_pub.publish(String(json.dumps(status, ensure_ascii=False)))


def main():
    rospy.init_node('color_pick')
    demo = Demo()
    rate = rospy.Rate(30)
    while not rospy.is_shutdown():
        demo.tick(rospy.get_time())
        rate.sleep()


if __name__ == '__main__':
    main()
