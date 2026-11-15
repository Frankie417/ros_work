"""ROS-independent perception, URDF FK and checked planar grasp IK.

The virtual camera is an explicitly calibrated, orthographic top-down camera.
Its detector receives pixels, not object colour names or object poses.
"""
import math
import xml.etree.ElementTree as ET
import cv2
import numpy as np

COLORS = ('red', 'yellow', 'blue', 'green')
BGR = {'red': (30, 30, 235), 'yellow': (20, 220, 240),
       'blue': (235, 85, 30), 'green': (50, 195, 40)}
CHINESE = dict(zip(COLORS, ('红色', '黄色', '蓝色', '绿色')))


def transform(xyz=(0, 0, 0), rpy=(0, 0, 0)):
    r, p, y = rpy
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    t = np.eye(4)
    t[:3, :3] = [[cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr],
                  [sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr], [-sp, cp*sr, cp*cr]]
    t[:3, 3] = xyz
    return t


class Arm:
    def __init__(self, xml, size):
        self.xml = ET.fromstring(xml)
        self.joints = self.xml.findall('joint')
        self.names = ['marm_mod_joint%d' % i for i in range(1, 7)] + ['marm_mod_gripper_joint']
        self.by_name = {j.get('name'): j for j in self.joints}
        self.limits = np.array([[float(self.by_name[n].find('limit').get(k))
                                for k in ('lower', 'upper')] for n in self.names])
        # Reject other models instead of silently applying this arm's analytic IK.
        for n, axis in zip(self.names[:6], ('0 0 1', '0 1 0', '0 1 0', '0 1 0', '0 0 1', '1 0 0')):
            assert self.by_name[n].find('axis').get('xyz') == axis, n
        self.size = size
        self.object_local = np.array([.123, 0, size/2, 1.])
        self.grip = -math.atan(size / (.123-size/2-.049))
        self.open = -.95
        self.home = np.array([.23, 0, .06+size/2+.06])

    def fk(self, q):
        values = dict(zip(self.names, q))
        frames = {'marm_mod_base_link': np.eye(4)}
        todo = list(self.joints)
        while todo:
            progress = False
            for j in list(todo):
                parent = j.find('parent').get('link')
                if parent not in frames:
                    continue
                o = j.find('origin')
                xyz = [float(v) for v in o.get('xyz', '0 0 0').split()]
                rpy = [float(v) for v in o.get('rpy', '0 0 0').split()]
                t = frames[parent] @ transform(xyz, rpy)
                if j.get('type') != 'fixed':
                    axis = np.array([float(v) for v in j.find('axis').get('xyz').split()])
                    a = values[j.get('name')]
                    cross = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
                    rotation = np.eye(4)
                    rotation[:3, :3] = np.eye(3) + math.sin(a)*cross + (1-math.cos(a))*(cross@cross)
                    t = t @ rotation
                frames[j.find('child').get('link')] = t
                todo.remove(j)
                progress = True
            if not progress:
                raise ValueError('Invalid URDF tree')
        return frames

    def object_pose(self, q):
        t = self.fk(q)['marm_mod_gripper_stator']
        return (t @ self.object_local)[:3], t[:3, :3]

    def ik(self, position, grip=None):
        x, y, z = position
        radial = math.hypot(x, y)-self.size/2
        height = z+.295-.130
        first, second = .300, math.hypot(.190, .050)
        cosine = (radial**2+height**2-first**2-second**2)/(2*first*second)
        if abs(cosine) > 1:
            raise ValueError('Target outside reachable workspace')
        delta = -math.acos(cosine)
        alpha = math.atan2(height, radial)-math.atan2(second*math.sin(delta), first+second*math.cos(delta))
        q2 = math.pi-alpha
        q3 = math.atan2(.050, .190)-math.pi-delta
        q = np.array([math.atan2(y, x), q2, q3, math.pi/2-q2-q3, 0, -math.pi/2,
                      self.open if grip is None else grip])
        if not np.all((q >= self.limits[:, 0]) & (q <= self.limits[:, 1])):
            raise ValueError('IK violates joint limits: %s' % q)
        actual, rotation = self.object_pose(q)
        if np.linalg.norm(actual-position) > 1e-7 or np.linalg.norm(rotation[:, 0]-[0, 0, -1]) > 1e-7:
            raise ValueError('IK/FK or downward grasp orientation mismatch')
        return q


class Camera:
    def __init__(self, config):
        self.config = config
        self.w, self.h = config['width'], config['height']

    def pixel(self, x, y):
        c = self.config
        return (int(round((y-c['y_min'])/(c['y_max']-c['y_min'])*(self.w-1))),
                int(round((c['x_max']-x)/(c['x_max']-c['x_min'])*(self.h-1))))

    def world(self, u, v):
        c = self.config
        return [c['x_max']-v/(self.h-1)*(c['x_max']-c['x_min']),
                c['y_min']+u/(self.w-1)*(c['y_max']-c['y_min'])]

    def render(self, blocks, size, rotations=None):
        image = np.full((self.h, self.w, 3), 65, np.uint8)
        for color, position in blocks.items():
            x, y, _ = position
            rotation = np.eye(3) if rotations is None else rotations[color]
            corners = []
            for dx, dy in [(-1, -1), (-1, 1), (1, 1), (1, -1)]:
                corner = np.array([x, y, 0.]) + rotation @ np.array([dx*size/2, dy*size/2, 0.])
                corners.append(self.pixel(corner[0], corner[1]))
            cv2.fillConvexPoly(image, np.array(corners, np.int32), BGR[color])
        return image

    def detect(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        ranges = {'red': [(0, 10), (170, 179)], 'yellow': [(20, 35)],
                  'blue': [(95, 130)], 'green': [(40, 85)]}
        detections, debug = {}, image.copy()
        for color, intervals in ranges.items():
            mask = np.zeros(hsv.shape[:2], np.uint8)
            for lo, hi in intervals:
                mask |= cv2.inRange(hsv, (lo, 100, 80), (hi, 255, 255))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = [c for c in contours if cv2.contourArea(c) > 40]
            if not contours:
                continue
            c = max(contours, key=cv2.contourArea)
            m = cv2.moments(c)
            u, v = m['m10']/m['m00'], m['m01']/m['m00']
            detections[color] = self.world(u, v)
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(debug, (x-3, y-3), (x+w+3, y+h+3), (255, 255, 255), 2)
            cv2.putText(debug, color, (x, max(y-8, 18)), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        return detections, debug
