#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image, CompressedImage
from smarp_msgs.msg import camInfo
from cv_bridge import CvBridge
from math import *
import time

class cameraRec:
    def __init__(self):
        rospy.init_node("camera_rec")
        # rospy.Subscriber("/usb_cam/image_raw/",Image, self.img_CB)
        rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.img_CB)

        self.cam_pub = rospy.Publisher("/cam_rec", camInfo ,queue_size=1)
        self.cam_pub_msg = camInfo()
        self.bridge = CvBridge()

        self.yellow_lower = np.array([15, 80, 0])
        self.yellow_upper = np.array([45, 255, 255])
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])

        self.light_upper_left_pt = (0, 0)
        self.light_lower_right_pt = (240, 320)

        self.light_color = ''

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
        
    def traffic_light(self, img) :
        light_crop_img = img.copy()[self.light_upper_left_pt[1]:self.light_lower_right_pt[1], 
                                    self.light_upper_left_pt[0]:self.light_lower_right_pt[0]]
        
        light_hsv = cv2.cvtColor(light_crop_img, cv2.COLOR_BGR2HSV)

        # red_lower = np.array([0, 120, 255])  
        # red_upper = np.array([20, 180, 255])  
        # mask_red = cv2.inRange(light_hsv,red_lower,red_upper)
        # red_lower1 = np.array([10, 70, 50])  
        # red_upper1 = np.array([10, 255, 255])  
        red_lower2 = np.array([0, 195, 146])  
        red_upper2 = np.array([14, 255, 255])  
        # mask_red1 = cv2.inRange(light_hsv,red_lower1,red_upper1)
        mask_red2 = cv2.inRange(light_hsv,red_lower2,red_upper2)
        red_detected = np.any(mask_red2)
        # blend_red = cv2.bitwise_and(light_hsv, light_hsv, mask=mask_red2)

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

        self.light_color = ''
        if red_detected :
            self.light_color += 'R'
        if green_detected :
            self.light_color += 'G'

        # self.light_color = ""
        # if green_color !=0:            
        #     self.light_color += "G"
        # if red_color != 0:        
        #     self.light_color += "R"

        # self.road_status.light = self.light_color
        # self.road_info.publish(self.road_status)
        # self.start_time = self.end_time

        # print(f'light_color={self.light_color}')
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
        crop_traffic_img = img.copy()[30:310, 0:190]


        blend_color = self.detect_color(crop_img)   # blend_color is HSV
        left_bc = blend_color.copy()[:, :320, :]
        right_bc = blend_color.copy()[:, 320:, :]

        left_binary = self.binary_image(left_bc)
        right_binary = self.binary_image(right_bc)

        self.rx, self.ry, self.rflag, self.rcount = self.calculateMoment(right_binary)
        self.lx, self.ly, self.lflag, self.lcount = self.calculateMoment(left_binary)

        if self.rx == 0 :
            self.rx = 320

        self.traffic_light(crop_traffic_img)

        # print(f'(lx={self.lx}, ly={self.ly}), (rx={self.rx},ry={self.ry})')
        
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
        self.cam_pub.publish(self.cam_pub_msg)
        
                
if __name__ == '__main__':
    try:
        cr = cameraRec()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    except ZeroDivisionError:
        pass
        