#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import cv2
from jetracer.nvidia_racecar import NvidiaRacecar
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import numpy as np

class controller:
    def __init__(self):
        rospy.init_node("timelap")
        self.car = NvidiaRacecar()
        
        ####################  Camera  ####################
        
        self.bridge = CvBridge()
        self.yellow_lower = np.array([15, 80, 0])
        self.yellow_upper = np.array([45, 255, 255])
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])
        self.light_upper_left_pt = (0, 0)
        self.light_lower_right_pt = (240, 320)
        
        #################### Variable ####################
        self.roi_left = 170
        self.roi_right = 470
        self.center_point = 150
        self.denominator = 450
        # self.input_speed = 0
        
        rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.img_CB)


        ####################  Line  ####################
        self.cx = 180
        rospy.Timer(rospy.Duration(1.0/10), self.timer_CB)
        
    
    
    def img_CB(self,data):
        # img = self.bridge.imgmsg_to_cv2(data)
        img = self.bridge.compressed_imgmsg_to_cv2(data)

        crop_img = img.copy()[300:, self.roi_left:self.roi_right]

        blend_color = self.detect_color(crop_img)   # blend_color is HSV
        center_binary = self.binary_image(blend_color)
        
        self.cx, self.cy = self.calculateMoment(center_binary)
        print(self.cx)


        # cv2.waitKey(1)

    
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

    def setLightROI(self, left_upper=(0,0), right_lower=(240,240)) :
        self.light_upper_left_pt = left_upper
        self.light_lower_right_pt = right_lower
        

    
    def binary_image(self, blend_color) :
        bin = cv2.cvtColor(blend_color, cv2.COLOR_BGR2GRAY)
        binary_line = np.zeros_like(bin)
        binary_line[bin != 0] = 1

        return binary_line
    
    
    def calculateMoment(self, img):
        x = 0
        y = 0

        ML = cv2.moments(img)
        if ( ML['m00'] > 0 ) :
            x = int(ML['m10']/ML['m00'])
            y = int(ML['m01']/ML['m00'])

        return x, y
       
    
    def jet_Control(self, steer, speed) :
        self.car.throttle = speed/1000
        self.car.steering = steer

    def Lane_follow_driving(self, speed=0) :
        
        steering = (self.cx - self.center_point) / self.denominator
        # print(self.cx)
        
        if steering > 1:
            steering = 1

        elif steering < -1:
            steering = -1
            
        self.car.throttle = speed/1000
        self.car.steering = steering
        
        self.jet_Control(steering, speed)



    def timer_CB(self, event):
        # Drive
        self.Lane_follow_driving(145)
        
        
if __name__ == "__main__":
    try:
        ct = controller()
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
