#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image, CompressedImage, LaserScan
from smarp_msgs.msg import camInfo, objectStatus, objInfo, lidarStatus
from cv_bridge import CvBridge
from math import *
import time

class Sensor:
    def __init__(self):
        rospy.init_node("camera_rec")

        # self.yellow_lower = np.array([15, 80, 0])
        # self.yellow_upper = np.array([45, 255, 255])
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])

        # self.light_upper_left_pt = (300, 0)
        # self.light_lower_right_pt = (620, 240)

        self.light_color = ''
        self.stop_line_flag = 0

        # limit distance : 95cm
        self.lidar_dist = 0.7
        self.lidar_range = [929,1017]
        self.grouping_size_limit = 0.1
        self.grouping_min_deg = 10
        # self.index_per_deree_10 = 32    # 10도 당 갯수
        # self.start_angle_index = 544    # 측정 각도 시작 index
        # self.end_angle_index = 609      # 측정 각도 끝 index

        self.lidar_range_half = 973

        rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.img_CB)
        rospy.Subscriber("/scan", LaserScan, self.lidar_callback)       
        rospy.Subscriber("/lidar_range", lidarStatus, self.lidar_status_callback)

        self.obj_pub = rospy.Publisher("/obj_scan", objectStatus, queue_size = 1)
        self.objects_pub = objectStatus()

        self.cam_pub = rospy.Publisher("/cam_rec", camInfo ,queue_size=1)
        self.cam_pub_msg = camInfo()
        self.bridge = CvBridge()


    def detect_color(self, img) :
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Threshold the HSV image to get only yellow colors
        # yellow_mask = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)

        # Threshold the HSV image to get only white colors
        white_mask = cv2.inRange(hsv, self.white_lower, self.white_upper)

        # Threshold the HSV image to get blend colors
        blend_mask = cv2.bitwise_or(white_mask, white_mask)
        blend_color = cv2.bitwise_and(hsv, hsv, mask=blend_mask)
        
        return blend_color

    # def setLightROI(self, left_upper=(0,0), right_lower=(240,240)) :
    #     self.light_upper_left_pt = left_upper
    #     self.light_lower_right_pt = right_lower
        
    def traffic_light(self, img) :
        # light_crop_img = img.copy()[self.light_upper_left_pt[1]:self.light_lower_right_pt[1], 
        #                             self.light_upper_left_pt[0]:self.light_lower_right_pt[0]]
        light_crop_img = img
        
        light_hsv = cv2.cvtColor(light_crop_img, cv2.COLOR_BGR2HSV)

        red_lower = np.array([0, 195, 146])  
        red_upper = np.array([5, 255, 255])  
        mask_red = cv2.inRange(light_hsv,red_lower,red_upper)
        red_detected = np.any(mask_red)
        blend_red = cv2.bitwise_and(light_hsv, light_hsv, mask=mask_red)

        # result_red = cv2.bitwise_and(light_hsv,light_hsv,mask = mask_red)
        
        # red_color = round(result_red.mean(),3)  

        # green_lower = np.array([66, 185, 138])  
        # green_upper = np.array([85, 255,255])  
        
        # Green detected
        # green_lower = np.array([90, 100, 80])  
        # green_upper = np.array([150, 255,255])  
        
        green_lower = np.array([70, 160, 148])  
        green_upper = np.array([84, 255,255])  
        mask_green = cv2.inRange(light_hsv,green_lower,green_upper)
        green_detected = np.any(mask_green)
        # blend_green = cv2.bitwise_and(light_hsv, light_hsv, mask=mask_green)

        
        # result_green = cv2.bitwise_and(light_hsv,light_hsv,mask = mask_green)       
        # green_color = round(result_green.mean(),3)

        blue_lower = np.array([105, 180, 170])  
        blue_upper = np.array([109,215,255])  
        mask_blue = cv2.inRange(light_hsv,blue_lower,blue_upper)
        blue_detected = np.any(mask_blue)
        blend_blue = cv2.bitwise_and(light_hsv, light_hsv, mask=mask_blue)


        self.light_color = ''
        if red_detected :
            self.light_color += 'R'
        if green_detected :
            self.light_color += 'G'
        if blue_detected :
            self.light_color += 'B'

        # self.light_color = ""
        # if green_color !=0:            
        #     self.light_color += "G"
        # if red_color != 0:        
        #     self.light_color += "R"

        # self.road_status.light = self.light_color
        # self.road_info.publish(self.road_status)
        # self.start_time = self.end_time

        #print(f'light_color={self.light_color}')
        # Show Image ========================
        # cv2.namedWindow("img", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("img", img)
        # cv2.namedWindow("light_crop_img", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("light_crop_img", light_crop_img)
        # cv2.namedWindow("light_hsv", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("light_hsv", light_hsv)
        # cv2.namedWindow("blend_green", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("blend_green", blend_green)
        # cv2.namedWindow("blend_red", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("blend_red", blend_red)
        # cv2.namedWindow("blend_blue", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("blend_blue", blend_blue)
        # cv2.waitKey(1)

    def binary_image(self, blend_color) :
        bin = cv2.cvtColor(blend_color, cv2.COLOR_BGR2GRAY)
        binary_line = np.zeros_like(bin)
        binary_line[bin != 0] = 1

        return binary_line

    
    def calculateMoment(self, img):
        x = 0
        y = 0
        dlflag = False
        count = 0

        ML = cv2.moments(img)
        if ( ML['m00'] > 0 ) :
            x = int(ML['m10']/ML['m00'])
            y = int(ML['m01']/ML['m00'])
            dlflag = True

        return x, y, dlflag, count
    
    
    def img_CB(self,data):
        # img = self.bridge.imgmsg_to_cv2(data)
        img = self.bridge.compressed_imgmsg_to_cv2(data)

        crop_img = img.copy()[300:, :]
        # crop_traffic_img = img.copy()[90:230, :640]
        # crop_traffic_img = img.copy()[90:230, 300:640]
        crop_traffic_img = img.copy()[80:230, 160:640]


        blend_color = self.detect_color(crop_img)   # blend_color is HSV
        left_bc = blend_color.copy()[:, :320, :]
        right_bc = blend_color.copy()[:, 320:, :]

        left_binary = self.binary_image(left_bc)
        right_binary = self.binary_image(right_bc)

        left_stopline_count = cv2.countNonZero(left_binary)
        # right_stopline_count = cv2.countNonZero(right_binary)
        # print(f"left_stop_line_count = {left_stopline_count}")

        if left_stopline_count >= 10000 :
            self.stop_line_flag = 1
            # print(f"stop_line_flag = {self.stop_line_flag}")

        elif left_stopline_count < 10000:
            self.stop_line_flag = 0
            # print(f"stop_line_flag = {self.stop_line_flag}")

        self.rx, self.ry, self.rflag, self.rcount = self.calculateMoment(right_binary)
        self.lx, self.ly, self.lflag, self.lcount = self.calculateMoment(left_binary)

        # if self.rx <= 10 :
            # self.rx = 320
        
        if self.rx == 0 :
            self.rx = 320


        # if self.lx <= 40 :
        #     self.lx = 0

        self.traffic_light(crop_traffic_img)

        # print(f'lx={self.lx}, rx={self.rx}')
        
        # print(f'shape={right_binary.shape}, rx={self.rx}, ry={self.ry}, rflag={self.rflag}, rcount={self.rcount}')
        # print(f'shape={left_binary.shape}, lx={self.lx}, ly={self.ly}, lflag={self.lflag}, lcount={self.lcount}')

        # cv2.circle(left_bc, (self.lx, self.ly), 3, (0, 255, 0), -1)
        # cv2.circle(right_bc, (self.rx, self.ry), 3, (0, 255, 0), -1)
        
        # cv2.namedWindow("left_bc", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("left_bc", left_bc)
        # cv2.namedWindow("right_bc", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("right_bc", right_bc)

        # cv2.waitKey(1)
        
        self.cam_pub_msg.m_point = [self.lx, self.rx]
        self.cam_pub_msg.light_color = self.light_color
        self.cam_pub_msg.stopline = self.stop_line_flag
        self.cam_pub.publish(self.cam_pub_msg)

    def lidar_status_callback(self, msg) :
        self.lidar_range = msg.range
        # self.index = self.lidar_range
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
        
    def filtering(self, right_angle, left_angle, distance):
        self.scan_msg.ranges = self.scan_msg.ranges[self.lidar_range_half:] + self.scan_msg.ranges[:self.lidar_range_half]
        obstacles = []
        # for index, value in enumerate(self.scan_msg.ranges):
            # trans_deg = index / 5.4
            # print(trans_deg)
            # if( (left_angle <= trans_deg <= right_angle) and value < distance):
                # obstacles.append([trans_deg, value])
            # if( (left_angle <= index <= right_angle) and value < distance ):
            #     obstacles.append([index, value])
        for index in range(right_angle, left_angle + 1):
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
        
                
if __name__ == '__main__':
    try:
        ss = Sensor()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    except ZeroDivisionError:
        pass
        
