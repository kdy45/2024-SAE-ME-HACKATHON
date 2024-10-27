#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from jetracer.nvidia_racecar import NvidiaRacecar
from smarp_msgs.msg import camInfo
import cv2
import numpy as np
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
from math import *
import time

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
        
        self.lx_center_point = 95
        self.rx_center_point = 240
        self.denominator = 470
        self.input_speed = 138
        self.stop_line_flag = False
        
        #################### cam ##################
        # self.cam_pub_msg = camInfo()
        self.bridge = CvBridge()

        self.yellow_lower = np.array([15, 80, 0])
        self.yellow_upper = np.array([45, 255, 255])
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])

        # self.light_upper_left_pt = (0, 0)
        # self.light_lower_right_pt = (240, 320)

        ####################  race  ####################
        # rospy.Subscriber("//usb_cam/image_raw/compressed", CompressedImage, self.cam_sub_CB)
        rospy.Subscriber("/usb_cam/image_raw/compressed",CompressedImage, self.img_CB)
        # self.cam_pub = rospy.Publisher("/cam_rec", camInfo ,queue_size=1)
        # rospy.Subscriber("/cam_rec", camInfo, self.cam_sub_CB)
        
        rospy.Timer(rospy.Duration(1.0/10), self.timer_CB)
        
    def detect_color(self, img) :
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Threshold the HSV image to get only yellow colors
        yellow_mask = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)

        # Threshold the HSV image to get only white colors
        white_mask = cv2.inRange(hsv, self.white_lower, self.white_upper)

        # Threshold the HSV image to get blend colors
        blend_mask = cv2.bitwise_or(yellow_mask, white_mask)
        blend_color = cv2.bitwise_and(hsv, hsv, mask=blend_mask)
        
        return blend_color

    # def setLightROI(self, left_upper=(0,0), right_lower=(240,240)) :
    #     self.light_upper_left_pt = left_upper
    #     self.light_lower_right_pt = right_lower
        

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

        # cv2.imshow("center line", crop_img)

        blend_color = self.detect_color(crop_img)   # blend_color is HSV
        # center_bc = blend_color.copy()[:,180:460]
        left_bc = blend_color.copy()[:, :320, :]
        right_bc = blend_color.copy()[:, 320:, :]
        
        # center_binary = self.binary_image(center_bc)
        left_binary = self.binary_image(left_bc)
        right_binary = self.binary_image(right_bc)

        right_stopline_count = cv2.countNonZero(right_binary)
        # print(right_stopline_count)
        
        if right_stopline_count >= 11000 :
            self.stop_line_flag = 1
            # print(f"stop_line_flag = {self.stop_line_flag}")

        elif right_stopline_count < 11000:
            self.stop_line_flag = 0
            # print(f"stop_line_flag = {self.stop_line_flag}")

        # self.cx, self.cy, self.cflag, self.ccount = self.calculateMoment(center_binary)
        self.rx, self.ry, self.rflag, self.rcount = self.calculateMoment(right_binary)
        self.lx, self.ly, self.lflag, self.lcount = self.calculateMoment(left_binary)
    

        if self.rx <= 0 :
            self.rx = 320

        # if self.lx <= 40 :
        #     self.lx = 0

        # self.cam_pub_msg.m_point = [self.lx, self.rx]
        # # self.cam_pub_msg.m_point = [self.cx]
        # self.cam_pub_msg.stopline = self.stop_line_flag
        
        # self.cam_pub.publish(self.cam_pub_msg)


        # if self.cx == 0 :
        #     self.cx = 320

        # cv2.waitKey(1)
        # cv2.imshow("right_binary",right_binary)
        # cv2.waitKey(1)

    # def cam_sub_CB(self, msg):
    #     self.lx = msg.m_point[0]
    #     self.rx = msg.m_point[1]
    #     self.stop_line_flag = msg.stopline
    #     # print(self.light_color)

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