#!/usr/bin/env python3

import rospy
import roslib
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Int32MultiArray
from cv_bridge import CvBridge

from math import *
import numpy as np
import cv2
from time import *

class TrafficLight :
    def __init__(self):
        self.bridge = CvBridge()
        rospy.init_node("Road_info")

        rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.img_CB)

        # lines, light, stopLine, labacorn, objects : True/False
        # self.infoCtrl = rospy.Subscriber("/recog_objs",RecogObj, self.road_CB)
        
        # Status of objects recognization ============
        # self.road_info = rospy.Publisher("/road_info", RoadInfo, queue_size=3)

        self.imgSizeX = 640
        self.imgSizeY = 480

        # Range of ROI for Traffic Light (Jetracer)
        self.light_upper_left_pt = (0, 0)
        self.light_lower_right_pt = (340, 240)

        # Detected Traffic Light Color
        self.light_color = ''
        # self.road_status = self.genRoadInfo()

        self.start_time = rospy.get_time()

    def setLightROI(self, left_upper=(0,0), right_lower=(240,240)) :
        self.light_upper_left_pt = left_upper
        self.light_lower_right_pt = right_lower
        
    def traffic_light(self, img) :
        light_crop_img = img.copy()[self.light_upper_left_pt[1]:self.light_lower_right_pt[1], 
                                    self.light_upper_left_pt[0]:self.light_lower_right_pt[0]]
        
        light_hsv = cv2.cvtColor(light_crop_img, cv2.COLOR_BGR2HSV)

        red_lower = np.array([0, 120, 255])  
        red_upper = np.array([15, 180, 255])  
        mask_red = cv2.inRange(light_hsv,red_lower,red_upper)
        result_red = cv2.bitwise_and(light_hsv,light_hsv,mask = mask_red)
        red_color = round(result_red.mean(),3)  

        green_lower = np.array([45, 185, 138])  
        green_upper = np.array([75, 255,255])  
        mask_green = cv2.inRange(light_hsv,green_lower,green_upper)
        result_green = cv2.bitwise_and(light_hsv,light_hsv,mask = mask_green)       
        green_color = round(result_green.mean(),3)

        self.light_color = ""
        if green_color !=0:            
            self.light_color += "G"
        if red_color != 0:        
            self.light_color += "R"

        # self.road_status.light = self.light_color
        # self.road_info.publish(self.road_status)
        # self.start_time = self.end_time

        print(f'light_color={self.light_color}')
        # Show Image ========================
        cv2.namedWindow("img", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("img", img)
        # cv2.namedWindow("light_crop_img", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("light_crop_img", light_crop_img)
        # cv2.namedWindow("light_hsv", cv2.WINDOW_AUTOSIZE)
        # cv2.imshow("light_hsv", light_hsv)
        cv2.waitKey(1)
        
    def img_CB(self, data) :
        img = self.bridge.compressed_imgmsg_to_cv2(data)

        self.traffic_light(img)

if __name__ == '__main__' :
    try :
        TrafficLight()
        rospy.spin()
    except rospy.ROSInterruptException :
        pass
      