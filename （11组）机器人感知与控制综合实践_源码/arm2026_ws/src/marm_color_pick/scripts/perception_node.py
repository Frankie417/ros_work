#!/usr/bin/env python3
"""Independent calibrated virtual-camera perception node; no hardware commands."""
import json
import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from perception_core import Detector, decode_bgr


class Perception:
    def __init__(self):
        self.detector = Detector(rospy.get_param('~camera'), source_x=rospy.get_param('~source_x'))
        self.result = rospy.Publisher('/color_pick/observations', String, queue_size=1)
        self.image = rospy.Publisher('/color_pick/perception_image', Image, queue_size=1)
        self.last_stamp = 0.
        rospy.Subscriber('/color_pick/image_raw', Image, self.receive, queue_size=1, buff_size=4*1024*1024)

    def receive(self, msg):
        try:
            stamp = msg.header.stamp.to_sec()
            if stamp <= self.last_stamp or not 0 <= rospy.get_time()-stamp <= .5:
                raise ValueError('Stale, future or repeated image timestamp')
            if msg.header.frame_id != 'virtual_overhead_camera':
                raise ValueError('Calibration is only valid for virtual_overhead_camera')
            image = decode_bgr(msg.data, msg.height, msg.width, msg.step, msg.encoding)
            start = time.perf_counter()
            result, debug = self.detector.detect(image)
            result.update(stamp=stamp, calibration='virtual_orthographic_v1',
                          processing_ms=(time.perf_counter()-start)*1000)
            self.last_stamp = stamp
            self.result.publish(String(json.dumps(result)))
            output = Image(header=msg.header, height=debug.shape[0], width=debug.shape[1],
                           encoding='bgr8', step=debug.shape[1]*3, data=debug.tobytes())
            self.image.publish(output)
        except (ValueError, TypeError) as error:
            self.detector.previous, self.detector.counts = {}, {}
            rospy.logwarn_throttle(2, 'Perception rejected frame: %s', error)


if __name__ == '__main__':
    rospy.init_node('color_perception')
    perception = Perception()
    rospy.spin()
