#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
import numpy as np
import socket
import threading
from sensor_msgs.msg import LaserScan
from smarp_msgs.msg import camInfo, objectStatus, objInfo, lidarStatus
from math import *

class Sensor:
    def __init__(self):
        rospy.init_node("camera_rec")

        # 색상 필터 범위
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])

        self.light_color = ''
        self.stop_line_flag = 0

        # 라이다 변수
        self.lidar_dist = 0.7
        self.lidar_range = [929,1017]
        self.grouping_size_limit = 0.1
        self.grouping_min_deg = 10
        self.lidar_range_half = 973

        # Lidar Scan Sub
        rospy.Subscriber("/scan", LaserScan, self.lidar_callback)       
        rospy.Subscriber("/lidar_range", lidarStatus, self.lidar_status_callback)

        self.obj_pub = rospy.Publisher("/obj_scan", objectStatus, queue_size = 1)
        self.cam_pub = rospy.Publisher("/cam_rec", camInfo ,queue_size=1)
        
        self.objects_pub = objectStatus()
        self.cam_pub_msg = camInfo()

        # BEV 변환 행렬
        src = np.float32([[150, 300], [490, 300], [20, 480], [620, 480]])
        dst = np.float32([[150, 0], [490, 0], [150, 480], [490, 480]])
        self.M = cv2.getPerspectiveTransform(src, dst)

        # UDP 통신
        
        self.udp_thread = threading.Thread(target=self.udp_receiver)
        self.udp_thread.daemon = True
        self.udp_thread.start()

    # ================= UDP 스트리밍 수신 =================
    def udp_receiver(self):
        UDP_IP = "0.0.0.0"
        UDP_PORT = 5000
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        rospy.loginfo(f"UDP Socket Binded on Port {UDP_PORT}. Waiting for Images...")

        while not rospy.is_shutdown():
            try:
                data, _ = sock.recvfrom(65536)
                np_arr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if img is not None:
                    self.process_image(img)
            except Exception as e:
                pass
                
    # ================= 이미지 파이프라인 =================
    def process_image(self, img):
        # 1. 신호등 인식
        crop_traffic_img = img.copy()[80:230, 160:640]
        self.traffic_light(crop_traffic_img)

        # 2. 색상 필터링 및 이진화
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        binary_mask = cv2.inRange(hsv, self.white_lower, self.white_upper)

        # 3. 정지선 인식
        left_stopline_count = cv2.countNonZero(binary_mask[300:, :320])
        self.stop_line_flag = 1 if left_stopline_count >= 10000 else 0

        # 4. BEV (조감도) 변환
        bev_img = cv2.warpPerspective(binary_mask, self.M, (640, 480), flags=cv2.INTER_LINEAR)

        # 5. 슬라이딩 윈도우 & 다항식 피팅
        target_dx, target_dy = self.sliding_window_and_target(bev_img)

        # 6. 제어 노드(Controller)로 데이터 전송
        self.cam_pub_msg.m_point = [target_dx, target_dy]
        self.cam_pub_msg.light_color = self.light_color
        self.cam_pub_msg.stopline = self.stop_line_flag
        self.cam_pub.publish(self.cam_pub_msg)

    def sliding_window_and_target(self, bev_img):
        histogram = np.sum(bev_img[240:, :], axis=0)
        midpoint = int(histogram.shape[0]/2)
        leftx_current = np.argmax(histogram[:midpoint])
        rightx_current = np.argmax(histogram[midpoint:]) + midpoint

        nwindows = 9
        window_height = int(bev_img.shape[0]/nwindows)
        margin = 50
        minpix = 30

        nonzero = bev_img.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])

        left_lane_inds, right_lane_inds = [], []

        for window in range(nwindows):
            win_y_low = bev_img.shape[0] - (window+1)*window_height
            win_y_high = bev_img.shape[0] - window*window_height
            
            # 왼쪽 차선 윈도우
            win_xleft_low = leftx_current - margin
            win_xleft_high = leftx_current + margin
            good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
                              (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
            left_lane_inds.append(good_left_inds)
            if len(good_left_inds) > minpix: leftx_current = int(np.mean(nonzerox[good_left_inds]))

            # 오른쪽 차선 윈도우
            win_xright_low = rightx_current - margin
            win_xright_high = rightx_current + margin
            good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
                               (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]
            right_lane_inds.append(good_right_inds)
            if len(good_right_inds) > minpix: rightx_current = int(np.mean(nonzerox[good_right_inds]))

        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)

        target_dx, target_dy = 0.0, 0.0
        lookahead_y = 150  # 로봇 코앞(480)으로부터 330픽셀 앞
        
        # 다항식 피팅 및 타겟 포인트 계산
        if len(left_lane_inds) > 1000 and len(right_lane_inds) > 1000:
            left_fit = np.polyfit(nonzeroy[left_lane_inds], nonzerox[left_lane_inds], 2)
            right_fit = np.polyfit(nonzeroy[right_lane_inds], nonzerox[right_lane_inds], 2)
            
            left_target_x = left_fit[0]*lookahead_y**2 + left_fit[1]*lookahead_y + left_fit[2]
            right_target_x = right_fit[0]*lookahead_y**2 + right_fit[1]*lookahead_y + right_fit[2]
            
            target_x = (left_target_x + right_target_x) / 2.0
            
        elif len(left_lane_inds) > 1000: # 왼쪽 차선만 보일 때 (차선 폭을 약 300px로 가정)
            left_fit = np.polyfit(nonzeroy[left_lane_inds], nonzerox[left_lane_inds], 2)
            left_target_x = left_fit[0]*lookahead_y**2 + left_fit[1]*lookahead_y + left_fit[2]
            target_x = left_target_x + 150 # 차선 폭의 절반만큼 우측으로 보정
            
        elif len(right_lane_inds) > 1000: # 오른쪽 차선만 보일 때
            right_fit = np.polyfit(nonzeroy[right_lane_inds], nonzerox[right_lane_inds], 2)
            right_target_x = right_fit[0]*lookahead_y**2 + right_fit[1]*lookahead_y + right_fit[2]
            target_x = right_target_x - 150 # 차선 폭의 절반만큼 좌측으로 보정
        else:
            return 0.0, 0.0 # 차선이 아예 안 보이면 직진 유지 (0, 0 반환)

        # 로봇 중심좌표(하단 정중앙: x=320, y=480) 기준으로 상대 오차 계산
        target_dx = target_x - 320.0
        target_dy = 480.0 - lookahead_y
        
        return target_dx, target_dy

    # ================= 신호등 및 라이다 로직 =================
    def traffic_light(self, img):
        light_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red_detected = np.any(cv2.inRange(light_hsv, np.array([0, 195, 146]), np.array([5, 255, 255])))
        green_detected = np.any(cv2.inRange(light_hsv, np.array([70, 160, 148]), np.array([84, 255, 255])))
        blue_detected = np.any(cv2.inRange(light_hsv, np.array([105, 180, 170]), np.array([109, 215, 255])))

        self.light_color = ''
        if red_detected: self.light_color += 'R'
        if green_detected: self.light_color += 'G'
        if blue_detected: self.light_color += 'B'

    def lidar_status_callback(self, msg):
        self.lidar_range = msg.range
        self.lidar_dist = msg.dist

    def lidar_callback(self, msg):
        self.scan_msg = msg
        obstacles = self.filtering(self.lidar_range[0], self.lidar_range[-1], self.lidar_dist)
        self.objects_pub = self.grouping(obstacles, self.grouping_size_limit)
        self.obj_pub.publish(self.objects_pub)
        
    def filtering(self, right_angle, left_angle, distance):
        self.scan_msg.ranges = self.scan_msg.ranges[self.lidar_range_half:] + self.scan_msg.ranges[:self.lidar_range_half]
        obstacles = []
        for index in range(right_angle, left_angle + 1):
            if self.scan_msg.ranges[index] < distance:
                obstacles.append([index, self.scan_msg.ranges[index]])
        return obstacles
        
    def grouping(self, obstacles, size_limit):
        no_group, pre_obj_deg, pre_obj_dist = 0, 0, 0                 
        one_grp = objInfo()             
        obs_info = objectStatus()       
        
        for idx, [deg, dist] in enumerate(obstacles):
            if (pre_obj_deg == 0):                                                
                one_grp.deg.append(deg); one_grp.dist.append(dist); pre_obj_deg, pre_obj_dist = deg, dist; no_group += 1
            elif (idx == len(obstacles) - 1):                                      
                one_grp.deg.append(deg); one_grp.dist.append(dist); obs_info.objects.append(one_grp)
            elif (deg - pre_obj_deg) > self.grouping_min_deg or abs(pre_obj_dist - dist) > size_limit:    
                one_grp.deg.append(pre_obj_deg); one_grp.dist.append(pre_obj_dist); obs_info.objects.append(one_grp)
                one_grp = objInfo(); pre_obj_deg, pre_obj_dist = deg, dist; no_group += 1
                one_grp.deg.append(deg); one_grp.dist.append(dist)
            else:
                pre_obj_deg, pre_obj_dist = deg, dist
        obs_info.no_objects = no_group
        return obs_info
                
if __name__ == '__main__':
    try:
        ss = Sensor()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
