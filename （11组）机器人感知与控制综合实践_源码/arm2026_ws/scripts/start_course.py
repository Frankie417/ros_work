#!/usr/bin/env python3
"""Bound initial ROS XML-RPC connection waits for the course launch."""
import runpy
import socket
import sys

socket.setdefaulttimeout(2.)
sys.argv = ['roslaunch', 'marm_color_pick', 'course_project.launch']+sys.argv[1:]
runpy.run_path('/opt/ros/noetic/bin/roslaunch', run_name='__main__')
