#!/usr/bin/env python3
"""Read-only topic health check; optionally save one image explicitly."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2
import numpy as np
import rospy
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import String
from perception_core import decode_bgr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--require-webcam', action='store_true')
    parser.add_argument('--save-virtual-image', help='Save the last virtual-camera image, not the webcam')
    args = parser.parse_args(rospy.myargv()[1:])
    rospy.init_node('course_health_check', anonymous=True)
    latest, counts, arrived = {}, {}, {}
    topics = {'joints': ('/joint_states', JointState), 'image': ('/color_pick/image_raw', Image),
              'observations': ('/color_pick/observations', String), 'status': ('/color_pick/status', String)}
    if args.require_webcam:
        topics['webcam'] = ('/gesture/camera/image_raw', Image)

    def callback(msg, key):
        latest[key] = msg
        counts[key] = counts.get(key, 0)+1
        arrived[key] = time.monotonic()

    subscribers = [rospy.Subscriber(topic, kind, callback, callback_args=key, queue_size=1)
                   for key, (topic, kind) in topics.items()]
    deadline = time.monotonic()+10
    while not rospy.is_shutdown() and time.monotonic() < deadline:
        if all(counts.get(k, 0) >= 3 for k in topics):
            break
        rospy.sleep(.05)
    assert all(counts.get(k, 0) >= 3 and time.monotonic()-arrived[k] < 1.5 for k in topics), counts
    joints = latest['joints']
    assert len(joints.name) == len(joints.position) == 7 and np.isfinite(joints.position).all()
    images = {}
    for key in ('image', 'webcam'):
        if key not in latest:
            continue
        msg = latest[key]
        image = decode_bgr(msg.data, msg.height, msg.width, msg.step, msg.encoding)
        assert 0 <= rospy.get_time()-msg.header.stamp.to_sec() < 1.5
        images[key] = dict(width=msg.width, height=msg.height, encoding=msg.encoding,
                           frame_id=msg.header.frame_id)
        if key == 'image' and args.save_virtual_image:
            assert cv2.imwrite(args.save_virtual_image, image)
    observations = json.loads(latest['observations'].data)
    status = json.loads(latest['status'].data)
    assert observations['calibration'] == 'virtual_orthographic_v1'
    assert status['perception_source'] == 'ros_image_topic' and not status['error']
    assert 0 <= rospy.get_time()-observations['stamp'] < .5
    record = dict(result='PASS', message_counts=counts, images=images,
                  stable_colors=sorted(observations['stable']), state=status['state'],
                  scope='live ROS topic validation; real webcam preview does not measure table objects')
    Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2))
    print(json.dumps(record, ensure_ascii=False, indent=2))
    for sub in subscribers:
        sub.unregister()


if __name__ == '__main__':
    main()
