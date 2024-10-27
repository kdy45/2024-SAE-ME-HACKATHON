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
        self.lidar_obj_msg = objectStatus()
        self.lidar_status_msg = lidarStatus()
        self.num_objects = 0
        self.objects = objInfo()
        self.left_index = 940
        self.right_index = 1030
        self.lidar_distance = 0.95


        ####################  Line  ####################
        self.follow_line = 'L'
        self.rx = 260
        self.lx = 70
        self.stop_line_flag = False

        ####################  traffic  ####################
        self.light_color = ''
        
        ####################  Ultra  ####################
        self.ultra_distance_start = 100
        self.ultra_distance_F = 50
        self.ultra_distance_B = 20
        self.ultra_distance_L = 30
        self.ultra_distance_R = 30
        self.ultra_parking_flag = True
        self.parking_start_flag = True
        self.msg = Float32MultiArray()

        # self.msg[0] : Right
        # self.msg[1] : Left
        # self.msg[2] : Back 
        # self.msg[3] : Front

        self.blue_flag = True
        self.dynamic_done_flag = True
        self.static_count = 0


        ####################  variable  ####################
        
        # self.lx_center_point = 70
        # self.rx_center_point = 220
        # self.rx_center_point = 260
        # self.denominator = 400
        self.input_speed = 160
        
        self.lx_center_point = 60
        self.rx_center_point = 270
        self.denominator = 400

        ####################  race  ####################

        rospy.Subscriber("/cam_rec", camInfo, self.cam_sub_CB)
        rospy.Subscriber("/distance", Float32MultiArray, self.Ultra_CB)
        rospy.Subscriber("/obj_scan", objectStatus, self.Lidar_CB)
        self.lidar_data_pub = rospy.Publisher("/lidar_range", lidarStatus, queue_size=1)
        rospy.Timer(rospy.Duration(1.0/5), self.timer_CB)


    def Lidar_CB(self, msg):
        self.lidar_obj_msg = msg
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
        if self.static_count % 2 == False : #왼쪽 턴
            self.Lidar_data_change(743,980,0.5)
            
            while self.num_objects :
                self.jet_Control(-0.9,140)
            self.jet_Control(0,0)
            self.Lidar_data_change(310,390,0.5)
            
            while self.num_objects != True :
                self.jet_Control(0.5,140)

            self.Lidar_data_change(924,1022,0.95)
            self.follow_line = 'L'
            self.Lane_follow_driving(145)

        elif self.static_count % 2 == True : #오른쪽 턴
            self.Lidar_data_change(980,1200,0.5)
            
            while self.num_objects :
                self.jet_Control(0.9,140)
            self.jet_Control(0,0)
            self.Lidar_data_change(1555,1610,0.5)
            
            while self.num_objects != True :
                self.jet_Control(-0.5,140)
                
            self.Lidar_data_change(924,1022,0.95)
            self.follow_line = 'R'
            self.Lane_follow_driving(145)
            
    
    def Ultra_CB(self, msg):
        if len(msg.data) >= 4:
            self.ultra_data = msg.data[:4]
        else:
            rospy.logwarn("Received Float32MultiArray dose not contain enough data")
     
     
    ##################유찬 주차 구상 지워도됨########################
    # def parking_yuyu(self):
    #     if self.blue_flag:
    #         self.jet_Control(0.0, 145)

    #         start_time = rospy.get_time()
    #         end_time = rospy.get_time()
    #         while end_time - start_time <= 1:
    #             self.jet_Control(0.0, 0.0)
    #             end_time = rospy.get_time()

    #         self.jet_Control(0.0, 0)

    #         start_time = rospy.get_time()
    #         end_time = rospy.get_time()
    #         while end_time - start_time <= 1:
    #             self.jet_Control(0.0, 0.0)
    #             end_time = rospy.get_time()

    #         while True:
    #             if self.distance[2] > 10:
    #                 self.jet_Control(-1.0, 150)
    #             else : 
    #                 self.jet_Control(0, 0)
    #                 self.blue_flag = False
    #                 self.parkgin_done_flag = True
    #                 break

                
    #         if self.parkgin_done_flag == True :
    #             self.jet_Control(-1.0, 150)
    ###############################################################
     
    def Parking_test(self):
        # print(self.ultra_data[1])
        # print(self.distances[1])
        # if self.ultra_parking_flag :
        #     if self.ultra_data[1] > 43:
        #         self.parking_start_flag = True
        
        # if 30 <= self.ultra_data[1] <= 38:
        #     self.ultra_parking_flag = True
        
        
        # if self.parking_start_flag:
        #     self.jet_Control(1.0,-200)

        #     if self.objects <= 10:
        #         self.jet_Control(0.0, 0.0)
        #         start_time = rospy.get_time()
        #         end_time = rospy.get_time()
        #         # while end_time - start_time <= 4:
        #         #     self.jet_Control(0.0, 0.0)
                    
            
        # if self.parking_start_flag:
        #     self.jet_Control(0,0)
        #     start_time = rospy.get_time()
        #     end_time = rospy.get_time()
        #     while end_time - start_time <= 4:
        #         self.jet_Control(0,0)
        #         end_time = rospy.get_time()
        #     self.Lidar_data_change(1693, 1768, 0.25)
        #     print(self.objects)
        
        # if self.object[1] > 23:
        #     self.jet_Control(0,0)
        #     while self.ultra_data[2] <= 12:
        #         self.jet_Control(-1, -200)
        #     if self.ultra_data[2] <= 11:
        #         self.jet_Control(0, 0)
        #         start_time = rospy.get_time()
        #         end_time = rospy.get_time()
        #         while end_time - start_time <= 4:
        #             self.jet_Control(0,0)
        
        # if self.blue_flag
        
                    
                
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
        self.Lane_follow_driving(145)

        # Traffic light
        if self.light_color == ('R' or 'RB'): #신호등 미션
            while self.light_color == ('R' or 'RB'):
                self.jet_Control(0,0)
        elif self.light_color == ('G' or ''):
            self.Lane_follow_driving(145)
        else:
            pass

        # Dynamic 
        if self.blue_flag and self.num_objects:
            while self.num_objects :
                self.jet_Control(0,0)

            self.blue_flag == False
            self.dynamic_done_flag == True
            # self.Object_detect()

        # Static
        if (self.blue_flag == False) and self.dynamic_done_flag and self.num_objects :
            self.jet_Control(0,0)
            print("static")
            start_time = rospy.get_time()
            end_time = rospy.get_time()

            while end_time - start_time <= 2:
                self.jet_Control(0,0)
                end_time = rospy.get_time()

            self.static_count += 1
            self.Avoid_static()

        # if self.ultra_data[3] <= self.ultra_distance_start:
        #     self.Ultra_CB()
        
        #Parking
        if self.blue_flag and self.dynamic_done_flag:
            self.Parking_test()



if __name__ == "__main__":
    try:
        ct = controller()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
