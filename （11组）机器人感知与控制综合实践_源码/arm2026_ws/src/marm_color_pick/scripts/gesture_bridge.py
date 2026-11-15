#!/usr/bin/env python3
"""Authenticated localhost bridge: Windows gesture labels -> virtual ROS scene."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import threading
import time
import uuid
import cv2
import numpy as np
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import Trigger

COLORS = ('red', 'yellow', 'blue', 'green')


class Bridge:
    def __init__(self):
        self.lock = threading.Lock()
        self.status, self.updated = {}, 0.
        self.pending, self.pending_since = None, 0.
        self.receipts = {}
        self.token, self.session = secrets.token_urlsafe(32), str(uuid.uuid4())
        self.pub = rospy.Publisher('/color_pick/command', String, queue_size=1)
        self.camera_pub = rospy.Publisher('/gesture/camera/image_raw', Image, queue_size=1)
        rospy.Subscriber('/color_pick/status', String, self.receive)

    def receive(self, msg):
        data = json.loads(msg.data)
        with self.lock:
            self.status, self.updated = data, time.monotonic()
            if self.pending and self.pending['color'] in ([data.get('active')]+data.get('queue', [])+data.get('completed', [])):
                self.pending = None

    def snapshot(self):
        with self.lock:
            fresh = time.monotonic()-self.updated < 1.5
            s = self.status.copy()
            ready = (fresh and s.get('mode') == 'kinematic_virtual_camera'
                     and not s.get('active') and not s.get('queue') and not s.get('error')
                     and self.pending is None and self.pub.get_num_connections() > 0)
            return dict(ready=ready, fresh=fresh, simulation_only=True, session=self.session,
                        pending=self.pending, robot=s)

    def submit(self, data):
        color, ident = data.get('color'), data.get('request_id')
        if color not in COLORS or not isinstance(ident, str) or not 8 <= len(ident) <= 64:
            raise ValueError('Invalid colour or request_id')
        with self.lock:
            if ident in self.receipts:
                return self.receipts[ident]
        if data.get('session') != self.session:
            raise ValueError('Bridge restarted; reconnect before confirming')
        # HTTPServer serializes submissions with this lock against callback state updates.
        with self.lock:
            s = self.status
            if (time.monotonic()-self.updated >= 1.5 or s.get('mode') != 'kinematic_virtual_camera'
                    or s.get('active') or s.get('queue') or s.get('error') or self.pending
                    or self.pub.get_num_connections() == 0):
                raise ValueError('Virtual arm busy, stale, pending or disconnected')
            if color in s.get('completed', []):
                raise ValueError('This colour is already sorted; reset the virtual scene first')
            self.pending = dict(color=color, request_id=ident)
            self.pending_since = time.monotonic()
            receipt = dict(accepted=True, color=color, request_id=ident, simulation_only=True)
            self.receipts[ident] = receipt
            if len(self.receipts) > 256:
                del self.receipts[next(iter(self.receipts))]
            self.pub.publish(String(color))
            rospy.loginfo('手势确认：%s（仅虚拟场景）', color)
            return receipt


def main():
    rospy.init_node('arm_gesture_bridge')
    bridge = Bridge()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # No token or image data in access logs.

        def reply(self, code, data):
            payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def authorized(self):
            supplied = self.headers.get('X-Arm-Gesture-Token', '')
            if not secrets.compare_digest(supplied, bridge.token):
                self.reply(403, dict(error='Authentication required'))
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            if self.path != '/status':
                return self.reply(404, dict(error='Not found'))
            self.reply(200, bridge.snapshot())

        def do_POST(self):
            if not self.authorized():
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                self.connection.settimeout(1.)
                if self.path == '/camera':
                    if not rospy.get_param('~allow_camera_preview', False):
                        return self.reply(403, dict(error='Local image preview is disabled'))
                    if not 0 < size <= 256*1024 or self.headers.get('Content-Type') != 'image/jpeg':
                        raise ValueError('Invalid preview image size or type')
                    data = self.rfile.read(size)
                    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                    if image is None or image.shape != (480, 640, 3):
                        raise ValueError('Preview requires a 640x480 BGR image')
                    msg = Image()
                    msg.header.stamp, msg.header.frame_id = rospy.Time.now(), 'gesture_webcam'
                    msg.height, msg.width, msg.encoding, msg.step = 480, 640, 'bgr8', 640*3
                    msg.data = image.tobytes()
                    bridge.camera_pub.publish(msg)
                    return self.reply(200, dict(accepted=True, simulation_only=True))
                if not 0 < size <= 2048:
                    raise ValueError('Invalid body size')
                data = json.loads(self.rfile.read(size))
                if self.path == '/command':
                    return self.reply(202, bridge.submit(data))
                if self.path == '/reset':
                    if not bridge.snapshot()['ready']:
                        raise ValueError('Reset requires an idle, connected virtual arm')
                    rospy.wait_for_service('/color_pick/reset', timeout=1)
                    response = rospy.ServiceProxy('/color_pick/reset', Trigger)()
                    return self.reply(200, dict(success=response.success, message=response.message))
                self.reply(404, dict(error='Not found'))
            except (ValueError, TypeError, OSError, cv2.error, rospy.ROSException, rospy.ServiceException) as error:
                self.reply(409, dict(error=str(error)))

    # Single request thread avoids reset/command races; the ROS subscriber has its own thread.
    from http.server import HTTPServer
    server = HTTPServer(('127.0.0.1', rospy.get_param('~port', 8796)), Handler)
    server.timeout = .2
    config = Path.home()/'.ros/arm2026_gesture_bridge.json'
    config.parent.mkdir(exist_ok=True)
    if config.exists():
        backup = config.with_name(config.stem+'.'+str(time.time_ns())+'.bak')
        shutil.copy2(config, backup)
        backup.chmod(0o600)
    fd = os.open(str(config), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(dict(url='http://127.0.0.1:%d' % server.server_port, token=bridge.token,
                       session=bridge.session, simulation_only=True), stream)
    config.chmod(0o600)
    rospy.loginfo('仅本机手势桥接已启动，连接文件：%s；图像预览=%s', config,
                  rospy.get_param('~allow_camera_preview', False))
    try:
        while not rospy.is_shutdown():
            server.handle_request()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
