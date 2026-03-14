#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import math
import numpy as np
from jetracer.nvidia_racecar import NvidiaRacecar
from smarp_msgs.msg import objectStatus, lidarStatus, camInfo
from std_msgs.msg import Float32MultiArray
import time

class controller:
    def __init__(self):
        rospy.init_node("controller")

        self.car = NvidiaRacecar()

        # 목표 지점 상대 좌표
        self.target_dx = 0.0
        self.target_dy = 0.0
        
        # PD 제어를 위한 이전 조향각 상태 저장
        self.prev_steering_rad = 0.0

        # Lidar, Ultra, Traffic 변수 초기화
        self.lidar_status_msg = lidarStatus()
        self.num_objects = 0
        self.light_color = ''
        self.stop_line_flag = False
        self.blue_flag = False
        self.dynamic_done_flag = False
        self.static_count = 0

        # ROS 통신 설정
        rospy.Subscriber("/cam_rec", camInfo, self.cam_sub_CB)
        rospy.Subscriber("/distance", Float32MultiArray, self.Ultra_CB)
        rospy.Subscriber("/obj_scan", objectStatus, self.Lidar_CB)
        self.lidar_data_pub = rospy.Publisher("/lidar_range", lidarStatus, queue_size=1)
        
        # 10Hz 메인 제어 루프
        rospy.Timer(rospy.Duration(1.0/10), self.timer_CB)

    # ================= ROS Callbacks =================
    def cam_sub_CB(self, msg):
        self.target_dx = msg.m_point[0]
        self.target_dy = msg.m_point[1]
        self.light_color = msg.light_color
        self.stop_line_flag = msg.stopline
        if self.light_color == 'B':
            self.blue_flag = True 

    def Lidar_CB(self, msg):
        self.num_objects = msg.no_objects
        self.objects = msg.objects
        
    def Ultra_CB(self, msg):
        if len(msg.data) >= 4:
            self.ultra_data = msg.data[:4]

    def Lidar_data_change(self, right_angle_index, left_angle_index, distance):
        self.lidar_status_msg.range = [right_angle_index, left_angle_index]
        self.lidar_status_msg.dist = distance
        self.lidar_data_pub.publish(self.lidar_status_msg)

    # ================= Actuator Control =================
    def jet_Control(self, steer, speed):
        self.car.throttle = speed / 1000.0
        self.car.steering = steer

    # ================= Pure Pursuit + PD Control =================
    def Lane_follow_driving(self, speed=0):
        if self.stop_line_flag: 
            self.target_dx += 50.0 

        # 1. 룩어헤드 거리 (Ld) 계산
        Ld = math.hypot(self.target_dx, self.target_dy)
        if Ld < 1.0: 
            Ld = 1.0 

        # 2. 가상 휠베이스 (픽셀 단위 튜닝 파라미터)
        L = 120.0 
        
        # 3. Pure Pursuit Base 수식
        steering_rad = math.atan2(2.0 * L * self.target_dx, Ld**2)
        
        # 4. PD Controller 적용
        Kp = 1.5  # 조향 민감도
        Kd = 0.5  # 조향 진동 억제력

        p_term = Kp * steering_rad
        d_term = Kd * (steering_rad - self.prev_steering_rad)

        # 최종 조향각 산출
        steering_cmd = p_term + d_term
        self.prev_steering_rad = steering_rad

        steering_cmd = np.clip(steering_cmd, -1.0, 1.0)

        self.jet_Control(steering_cmd, speed)

    # ================= Mission Control =================
    def Avoid_static(self):
        if self.static_count % 2 == 1: 
            self.Lidar_data_change(743, 980, 0.5)
            while self.num_objects: self.jet_Control(-0.9, 140)
            self.jet_Control(0, 0)
            self.Lidar_data_change(310, 390, 0.5)
            while not self.num_objects: self.jet_Control(0.5, 140)
            self.Lidar_data_change(924, 1022, 0.95)
            self.Lane_follow_driving(145)

        elif self.static_count % 2 == 0: 
            self.Lidar_data_change(980, 1200, 0.5)
            while self.num_objects: self.jet_Control(0.9, 140)
            self.jet_Control(0, 0)
            self.Lidar_data_change(1555, 1610, 0.5)
            while not self.num_objects: self.jet_Control(-0.5, 140)
            self.Lidar_data_change(924, 1022, 0.95)
            self.Lane_follow_driving(145)

    def timer_CB(self, event):
        # 1. 기본 주행 추종
        self.Lane_follow_driving(145)

        # 2. 신호등 미션 처리
        if 'R' in self.light_color:
            while 'R' in self.light_color:
                self.jet_Control(0,0)
        elif 'G' in self.light_color or self.light_color == '':
            self.Lane_follow_driving(145)

        # 3. 동적 장애물 처리
        if self.blue_flag and self.num_objects:
            while self.num_objects:
                self.jet_Control(0,0)
            self.blue_flag = False
            self.dynamic_done_flag = True

        # 4. 정적 장애물 처리
        if not self.blue_flag and self.dynamic_done_flag and self.num_objects:
            self.jet_Control(0,0)
            start_time = rospy.get_time()
            while rospy.get_time() - start_time <= 2:
                self.jet_Control(0,0)
            self.static_count += 1
            self.Avoid_static()

if __name__ == "__main__":
    try:
        ct = controller()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
