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
        self.msg = Float32MultiArray()

        # self.msg[0] : Right
        # self.msg[1] : Left
        # self.msg[2] : Back 
        # self.msg[3] : Front

        self.blue_flag = False
        self.dynamic_done_flag = False
        self.static_count = 0


        ####################  variable  ####################
        
        self.lx_center_point = 60
        self.rx_center_point = 270

        self.denominator = 400
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
        if self.static_count % 2 == True : #왼쪽 턴
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

        elif self.static_count % 2 == False : #오른쪽 턴
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
            
            # start_time = rospy.get_time()
            # end_time = rospy.get_time()
            
            # while end_time - start_time <= 4:
            #     self.jet_Control(-0.6,145)
    # def parking(self):
    #     #if  ==
        
    
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
            print(f'RIRHG DETECT : lx={self.lx},rx={self.rx}, speed={speed}, steering={steering}')

        elif self.follow_line == 'L' :
            # 속도가 빠를 경우 분모를 키워준다
            # steering = (self.lx - 85) / 125
            # steering = (self.lx - 85) / 135
            if self.stop_line_flag :
                self.lx -= 70
            steering = (self.lx - self.lx_center_point) / self.denominator
            print(f'LEFT DETECT : lx={self.lx}, rx={self.rx}, speed={speed}, steering={steering}')
        
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
            # start_time = rospy.get_time()
            # end_time = rospy.get_time()

            # while end_time - start_time <= 1.5:
            #     self.jet_Control(-0.2,145)
            #     end_time = rospy.get_time()
            self.Lane_follow_driving(145)
        else:
            pass

        # Dynamic 
        '''
        반대쪽 초록색 화면 감지 안 하면 파란색 표지판 감지 잘 됨.
        파란색 감지되면 동적 장애물 인식 잘 됨.
        멈추고 없을 때 가는 것까지 완벽
        
        첫 번째 피하고 삐딱하게 정지해서 차선을 다른 것으로 감지해서 주행함.
        이때부터 라인을 못잡고 잡더라고 2차선으로 라인 바꾸고 주행하게 됨.
        '''
        if self.blue_flag and self.num_objects:
            while self.num_objects :
                self.jet_Control(0,0)

            self.blue_flag == False
            self.dynamic_done_flag == True
            # self.Object_detect()

        # Static
        '''
        멈추는 건 잘 되는데 멀리서 멈춤
        첫 번째는 멀어도 괜찮은데 두 번째 장애물은 조금 더 가까이에서 멈춰야 함.
        조향하는 건 코드가 먹혔음.
        '''
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
        # if self.blue_flag and self.dynamic_done_flag:
        #     self.parking()

        '''
        위 빨간 주석들을 제외하면 주행은 잘 됨.
        배터리가 낮아서 힘을 못 받아서 느리게 가긴 했지만 주행은 잘 됨.
        (동적은 확실하게 잘 되고 라인을 확실하게 잡았다는 가정하에
        정적도 잘 멈춘다. 피하는 코드가 안 되서 확인을 못함.
        정적을 다 피했다고 가정하면 라인 인식 주행은 완벽함.)
        
        주차하려고 코드를 돌리면 딜레이가 심하게 걸려서 느려짐.
        '''


if __name__ == "__main__":
    try:
        ct = controller()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
