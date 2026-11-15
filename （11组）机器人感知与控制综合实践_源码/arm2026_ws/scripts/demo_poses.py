#!/usr/bin/env python3
"""Publish virtual demonstration poses on /joint_states; no hardware interface."""
import argparse
import json
from pathlib import Path
import rospy
from sensor_msgs.msg import JointState


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pose',default='ready',help='pose name or all')
    parser.add_argument('--hold',type=float,default=4)
    parser.add_argument('--data',default=str(Path(__file__).resolve().parents[1]/'config/poses.json'))
    args=parser.parse_args()
    records=json.loads(Path(args.data).read_text())
    selected=[p for p in records if args.pose in ('all',p['name'])]
    if not selected:parser.error('Unknown pose')
    rospy.init_node('arm_pose_demo')
    pub=rospy.Publisher('/joint_states',JointState,queue_size=1)
    rate=rospy.Rate(20)
    while pub.get_num_connections()==0 and not rospy.is_shutdown():rate.sleep()
    for p in selected:
        msg=JointState();msg.name=p['joint_names'];msg.position=p['positions']
        end=rospy.Time.now()+rospy.Duration(args.hold)
        rospy.loginfo('Pose: %s',p['name'])
        while not rospy.is_shutdown() and rospy.Time.now()<end:
            msg.header.stamp=rospy.Time.now();pub.publish(msg);rate.sleep()


if __name__=='__main__':main()
