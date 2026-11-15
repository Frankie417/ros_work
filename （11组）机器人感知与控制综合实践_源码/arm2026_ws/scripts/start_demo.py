#!/usr/bin/env python3
"""Start RViz with bounded initial local master connection waits."""
import os
import runpy
import socket
import sys

socket.setdefaulttimeout(2)
os.environ.setdefault('ROS_MASTER_URI','http://127.0.0.1:11311')
os.environ.setdefault('ROS_HOSTNAME','127.0.0.1')
sys.argv=['roslaunch','--skip-log-check','marm_description','view_marm_modular.launch']
runpy.run_path('/opt/ros/noetic/bin/roslaunch',run_name='__main__')
