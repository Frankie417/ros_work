#!/usr/bin/env python3
"""Launch the existing Windows webcam client from a WSL ROS launch file."""
import json
from pathlib import Path
import subprocess
import time
import rospy


def main():
    rospy.init_node('windows_gesture_camera')
    python = Path(rospy.get_param('~python'))
    if not python.is_file():
        raise RuntimeError('Windows Python not found; set windows_python to an existing WSL path')
    config = Path.home()/'.ros/arm2026_gesture_bridge.json'
    started, deadline = time.time(), time.monotonic()+15
    while not rospy.is_shutdown():
        if config.exists() and config.stat().st_mtime >= started-2:
            try:
                json.loads(config.read_text())
                break
            except (ValueError, OSError):
                pass
        if time.monotonic() > deadline:
            raise RuntimeError('Timed out waiting for the new local bridge connection')
        rospy.sleep(.1)
    if rospy.is_shutdown():
        return
    client = Path(rospy.get_param('~client'))
    convert = lambda p: subprocess.check_output(['wslpath', '-w', str(p)], text=True).strip()
    process = subprocess.Popen([str(python), convert(client), '--connection', convert(config), '--publish-images'], cwd='/mnt/c')
    try:
        while not rospy.is_shutdown() and process.poll() is None:
            rospy.sleep(.2)
        if not rospy.is_shutdown() and process.poll() not in (None, 0):
            raise RuntimeError('Windows webcam client exited with code %s' % process.returncode)
    except rospy.ROSInterruptException:
        pass
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == '__main__':
    main()
