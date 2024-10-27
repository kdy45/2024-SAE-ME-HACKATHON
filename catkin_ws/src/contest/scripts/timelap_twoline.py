#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from jetracer.nvidia_racecar import NvidiaRacecar
from smarp_msgs.msg import camInfo
# from sensor_msgs.msg import CompressedImage

class timelap:
    def __init__(self):
        rospy.init_node("timelap_twoline")

        self.start_time = rospy.get_time()
        self.car = NvidiaRacecar()

        ####################  Line  ####################
        self.follow_line = 'R'
        self.rx = 220
        self.lx = 70

        ####################  variable  ####################
        
        # self.lx_center_point = 75
        # self.rx_center_point = 250
        
        self.lx_center_point = 85
        self.rx_center_point = 235


        self.denominator = 460
        self.input_speed = 138
        self.stop_line_flag = False

        ####################  race  ####################
        # rospy.Subscriber("//usb_cam/image_raw/compressed", CompressedImage, self.cam_sub_CB)
        rospy.Subscriber("/cam_rec", camInfo, self.cam_sub_CB)
        rospy.Timer(rospy.Duration(1.0/10), self.timer_CB)


    def cam_sub_CB(self, msg):
        self.lx = msg.m_point[0]
        self.rx = msg.m_point[1]
        self.stop_line_flag = msg.stopline
        # print(self.light_color)

    def jet_Control(self, steer, speed) :
        self.car.throttle = speed/1000
        # self.car.throttle = 0
        self.car.steering = steer

    def Lane_follow_driving(self, speed=0) :
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
            
        if steering > 0.25:
            steering = 0.25
        elif steering < -0.25:
            steering = -0.25
        # if self.detect_corner_speed():
        #     speed = 200

        self.jet_Control(steering, speed)
        

    def timer_CB(self, event):
        # Drive
        self.Lane_follow_driving(self.input_speed)


if __name__ == "__main__":
    try:
        tl = timelap()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass