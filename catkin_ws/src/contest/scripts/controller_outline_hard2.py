#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import os
from jetracer.nvidia_racecar import NvidiaRacecar
from smarp_msgs.msg import objectStatus, lidarStatus, objInfo, camInfo
from std_msgs.msg import Float32, Float32MultiArray, Int32MultiArray
import serial
import time

class controller:
    def __init__(self):
        rospy.init_node("controller")

        self.start_time = rospy.get_time()
        self.car = NvidiaRacecar()

        ####################  Lidar  ####################
        self.lidar_status_msg = lidarStatus()
        self.num_objects = 0
        self.left_index = 940
        self.right_index = 1030
        self.lidar_distance = 0.95
        self.traffic_count = False

        ####################  Line  ####################
        self.follow_line = 'R'
        self.rx = 250
        self.lx = 60
        self.stop_line_flag = False

        ####################  traffic  ####################
        self.light_color = ''
        self.traffic_count = 0
        
        ####################  Ultra  ####################
        self.ultra_distance_start = 100
        self.ultra_distance_F = 50
        self.ultra_distance_B = 20
        self.ultra_distance_L = 30
        self.ultra_distance_R = 30
        self.msg = Float32MultiArray()

        # self.msg[0] : Right
        # self.msg[1] : Left
        # self.msg[2] : Back 
        # self.msg[3] : Front

        self.blue_flag = False
        self.dynamic_done_flag = False
        self.static_count = 0


        ####################  variable  ####################
        # self.lx_center_point = 90
        self.lx_center_point = 100
        # self.rx_center_point = 240 #-> 2차선 시작_1, 카메라 세팅은 250으로
        self.rx_center_point = 235
        # self.lx_center_point = 80
        # self.rx_center_point = 220 # -> 2차선 시작_2
        # self.lx_center_point = 60
        # self.rx_center_point = 250 # -> 2차선 시작_3
       
        # self.denominator = 420 #-> 2차선 시작_1
        self.denominator = 430 # -> 2차선 시작_2
        # self.denominator = 460 # -> 2차선 시작_3
        self.input_speed = 160

        ####################  race  ####################

        rospy.Subscriber("/cam_rec", camInfo, self.cam_sub_CB)
        rospy.Subscriber("/distance", Float32MultiArray, self.Ultra_CB)
        rospy.Subscriber("/obj_scan", objectStatus, self.Lidar_CB)
        self.lidar_data_pub = rospy.Publisher("/lidar_range", lidarStatus, queue_size=1)
        rospy.Timer(rospy.Duration(1.0/5), self.timer_CB)


    def Lidar_CB(self, msg):
        self.num_objects = msg.no_objects
        self.objects = msg.objects
        # print(self.num_objects)
        
        
    def Lidar_data_change(self, right_angle_index, left_angle_index, distance):
        self.lidar_status_msg.range = [right_angle_index, left_angle_index]
        self.lidar_status_msg.dist = distance
        self.lidar_data_pub.publish(self.lidar_status_msg)
        
    # def Lidar_index_change(self):
    #     if(self.num_objects > 2):
    #         self.lidar_data_change(550, 600, 1.0)
    #     else:
    #         self.lidar_data_change(self.left_index, self.right_index, self.lidar_distance)
        
    # def Object_detect(self):
    #     # 파란색 표지판을 감지했을 때
    #     # 라이다에 물체가 인식되었을 때
    #     if self.num_objects == 1:
    #         # 잠시 멈춤
    #         self.Lane_follow_driving(0)
    #         try:
    #             # 현 시간대 인식된 물체 각도 가져오기
    #             self.pre_obs_deg_left = self.objects[0].deg[-1]
    #             self.pre_obs_deg_right = self.objects[0].deg[0]
    #             # rospy.loginfo(self.pre_obs_deg_left)
    #             s_time = rospy.get_time()
                
    #             while True:
    #                 end_time = rospy.get_time()
    #                 # 동적 판변을 위해 기다리기
    #                 if end_time - s_time >= 0.7 :
    #                     break
    #             # 현 시간대 인식된 물체 각도 가져오기
    #             self.cur_obs_deg_left = self.objects[0].deg[-1]
    #             self.cur_obs_deg_right = self.objects[0].deg[0]
    #             # rospy.loginfo(self.cur_obs_deg_left)
    #             # rospy.loginfo(f"{self.cur_obs_deg_left} - {self.pre_obs_deg_left} = {abs(self.cur_obs_deg_left - self.pre_obs_deg_left)}")
    #             # 동적 물체 인지_물체 피해가는 코드
    #             self.Object_type_decision()
    #         except IndexError:
    #             pass

    # def Object_type_decision(self):        
    #     if abs(self.cur_obs_deg_left - self.pre_obs_deg_left) > 6 or abs(self.cur_obs_deg_right - self.pre_obs_deg_right) > 6:
    #         print("dynamic")
    #         while self.num_objects == 1:
    #             print("car stop")
    #             if self.num_objects == 0:
    #                 self.blue_flag = False
    #                 self.dynamic_done_flag = True
    #         # 피해가기
    
    def Avoid_static(self):
        start_time = rospy.get_time()
        end_time = rospy.get_time()
        while end_time - start_time <= 1.5 :
            self.jet_Control(-0.5,150)
            end_time = rospy.get_time()
        
        start_time = rospy.get_time()
        end_time = rospy.get_time()
        while end_time - start_time <= 1.5 :
            self.jet_Control(0,0)
            end_time = rospy.get_time()

        start_time = rospy.get_time()
        end_time = rospy.get_time()
        while end_time - start_time <= 1.7 :
            self.jet_Control(0.5,158)
            end_time = rospy.get_time()

        self.follow_line = 'L'

        # self.Lane_follow_driving(145)

    def Ultra_CB(self, msg):
        if len(msg.data) >= 4:
            self.ultra_data = msg.data[:4]
            # print(f"Front : self.ultra_data[3]")
            # self.ultra_data[0] : Right
            # self.ultra_data[1] : Left
            # self.ultra_data[2] : Back 
            # self.ultra_data[3] : Front

            # if self.ultra_data[3] <= self.ultra_distance_F:
                # self.jet_Control(0,0)
                # self.jet_Control(0.3, 160)
                # rospy.sleep(3.5)
                # self.jet_Control(-0.3, 160)
                # rospy.sleep(3.3)
                # self.Lane_follow_driving(160)
        else:
            rospy.logwarn("Received Float32MultiArray dose not contain enough data")
     
     
    def cam_sub_CB(self, msg):
        self.lx = msg.m_point[0]
        self.rx = msg.m_point[1]
        self.light_color = msg.light_color
        self.stop_line_flag = msg.stopline
        if self.light_color == 'B':
            self.blue_flag = True 
        # print(self.light_color)

    def jet_Control(self, steer, speed) :
        self.car.throttle = speed/1000
        # self.car.throttle = 0
        self.car.steering = steer

    def Lane_follow_driving(self, speed=0) :
        # # Save the current time
        # self.end_time = rospy.get_time()

        # Send Control command in 10Hz 
        # if self.end_time - self.start_time >= 0.1:
        #     self.start_time = self.end_time
        #     steering = 0

        if self.lx == 0:
            self.follow_line = 'R'

        # if self.lx == 0:
        #     self.follow_line = 'R'     

        elif self.rx == 320:
            self.follow_line = 'L'

        if self.follow_line == 'R' :
            # 속도가 빠를 경우 분모를 키워준다
            # steering = (self.rx - 235) / 130
            if self.stop_line_flag :
                self.rx += 70
            steering = (self.rx - self.rx_center_point) / self.denominator
            # print(f'RIRHG DETECT : lx={self.lx},rx={self.rx}, speed={speed}, steering={steering}')

        elif self.follow_line == 'L' :
            # 속도가 빠를 경우 분모를 키워준다
            # steering = (self.lx - 85) / 125
            # steering = (self.lx - 85) / 135
            if self.stop_line_flag :
                self.lx -= 70
            steering = (self.lx - self.lx_center_point) / self.denominator
            # print(f'LEFT DETECT : lx={self.lx}, rx={self.rx}, speed={speed}, steering={steering}')
        
        else :
            steering = 0
        
        if steering > 1:
            steering = 1

        elif steering < -1:
            steering = -1
        # if self.detect_corner_speed():
        #     speed = 200

        self.jet_Control(steering, speed)
        

    def timer_CB(self, event):

        # rospy.loginfo("미션코드작성")

        # Drive
        self.Lane_follow_driving(140)

        # Traffic light
        if self.light_color == ('R' or 'RB' or 'RG'): #신호등 미션
            while self.light_color == ('R' or 'RB' or 'RG'):
                self.jet_Control(0,0)
            self.traffic_count = True
        elif self.light_color == ('G' or ''):
            # start_time = rospy.get_time()
            # end_time = rospy.get_time()

            # while end_time - start_time <= 1.5:
            #     self.jet_Control(-0.2,145)
            #     end_time = rospy.get_time()
            # self.Lane_follow_driving(145)
            pass
        else:
            pass

        # Dynamic 
        if self.blue_flag and self.num_objects and self.traffic_count and self.dynamic_done_flag == False :
            while self.num_objects:
                self.jet_Control(0,0)

            # start_time = rospy.get_time()
            # end_time = rospy.get_time()
            # while end_time - start_time <= 1.5 :
            #     self.jet_Control(0,0)
            #     end_time = rospy.get_time()

            self.blue_flag = False
            self.dynamic_done_flag = True
            # self.Object_detect()

        # Static
        if  self.dynamic_done_flag and self.num_objects :
            self.jet_Control(0,0)
            # print("static")
            start_time = rospy.get_time()
            end_time = rospy.get_time()

            while end_time - start_time <= 2:
                self.jet_Control(-0.8,0)
                end_time = rospy.get_time()
                
            # self.static_count += 1
            self.Avoid_static()
            while True:
                self.Lane_follow_driving(140)
                if self.stop_line_flag:
                    while True:
                        self.jet_Control(0,0)


if __name__ == "__main__":
    try:
        ct = controller()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
