#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from sensor_msgs.msg import LaserScan
from smarp_msgs.msg import objectStatus, objInfo, lidarStatus
import math
import time
# from numba import jit

class lidar_test():
    def __init__(self) :
        rospy.init_node("Lidar")
        rospy.Subscriber("/scan", LaserScan, self.lidar_callback)       
        rospy.Subscriber("/lidar_range", lidarStatus, self.lidar_status_callback) 
        self.obj_pub = rospy.Publisher("/obj_scan", objectStatus, queue_size = 1)
        self.objects_pub = objectStatus()
        # limit distance : 95cm
        self.lidar_dist = 0.95
        self.lidar_range = [935,1035]
        self.grouping_size_limit = 0.1
        self.grouping_min_deg = 3
        # self.index_per_deree_10 = 32    # 10도 당 갯수
        # self.start_angle_index = 544    # 측정 각도 시작 index
        # self.end_angle_index = 609      # 측정 각도 끝 index
        
        self.lidar_range_half = 973


    def lidar_status_callback(self, msg) :
        self.lidar_range = msg.range
        self.index = self.lidar_range
        self.lidar_dist = msg.dist


    def lidar_callback(self, msg):
        # start = time.time()
        self.scan_msg = msg
        obstacles = self.filtering(self.lidar_range[0], self.lidar_range[-1], self.lidar_dist)
        self.objects_pub = self.grouping(obstacles, self.grouping_size_limit)
        # print(self.objects_pub)
        self.obj_pub.publish(self.objects_pub)
        # end = time.time()
        # print(f"{end - start : .5f} sec")        
        
    def filtering(self, left_angle, right_angle, distance):
        self.scan_msg.ranges = self.scan_msg.ranges[self.lidar_range_half:] + self.scan_msg.ranges[:self.lidar_range_half]
        obstacles = []
        # for index, value in enumerate(self.scan_msg.ranges):
            # trans_deg = index / 5.4
            # print(trans_deg)
            # if( (left_angle <= trans_deg <= right_angle) and value < distance):
                # obstacles.append([trans_deg, value])
            # if( (left_angle <= index <= right_angle) and value < distance ):
            #     obstacles.append([index, value])
        for index in range(left_angle, right_angle + 1):
                if self.scan_msg.ranges[index] < distance:
                    obstacles.append([index, self.scan_msg.ranges[index]])
                # print(obstacles)
        return obstacles
        
        
    def grouping(self, obstacles, size_limit) :
        no_group = 0
        pre_obj_deg = 0                 # deg of previous point
        pre_obj_dist = 0                # dist of previous point
        one_grp = objInfo()             # deg=[ ], dist=[ ]
        obs_info = objectStatus()       # [one_Group, two_Group, ...]
        
        for idx, [deg, dist]  in enumerate(obstacles) :

            if (pre_obj_deg == 0) :                                                # 첫번째 Obj 정보 처리
                one_grp.deg.append(deg)
                one_grp.dist.append(dist)
                pre_obj_deg = deg
                pre_obj_dist = dist
                no_group += 1
            elif (idx == len(obstacles) - 1) :                                      # 마지막 Obj 정보 처리
                one_grp.deg.append(deg)
                one_grp.dist.append(dist)
                obs_info.objects.append(one_grp)

            elif (deg - pre_obj_deg) > self.grouping_min_deg or abs(pre_obj_dist - dist) > size_limit :    # 다른 물체인 경우 --> 이전 물체 등록, 새 물체 생성
                one_grp.deg.append(pre_obj_deg)
                one_grp.dist.append(pre_obj_dist) 
                obs_info.objects.append(one_grp)
                one_grp = objInfo()
                pre_obj_deg = deg
                pre_obj_dist = dist
                no_group += 1
                one_grp.deg.append(deg)
                one_grp.dist.append(dist)
            else :
                pre_obj_deg = deg
                pre_obj_dist = dist

        obs_info.no_objects = no_group

        # print(f'{obs_info}')

        return obs_info        

if __name__ == "__main__":
    try:
        lidar = lidar_test()
        rospy.spin()
        
    except rospy.ROSInterruptException:
        pass