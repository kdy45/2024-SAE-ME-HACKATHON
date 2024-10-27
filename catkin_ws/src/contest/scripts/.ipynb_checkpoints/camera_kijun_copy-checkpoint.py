#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import Int32MultiArray
from cv_bridge import CvBridge
from math import *

class cameraRec:
    def __init__(self):
        rospy.init_node("camera_rec")
        # rospy.Subscriber("/usb_cam/image_raw/",Image, self.img_CB)
        rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.img_CB)

        self.cam_pub = rospy.Publisher("/cam_rec",Int32MultiArray,queue_size=1)
        self.cam_pub_msg = Int32MultiArray()
        self.bridge = CvBridge()

        self.yellow_lower = np.array([15, 80, 0])
        self.yellow_upper = np.array([45, 255, 255])
        self.white_lower = np.array([0, 0, 200])
        self.white_upper = np.array([179, 64, 255])

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

        blend_color = self.detect_color(crop_img)   # blend_color is HSV
        left_bc = blend_color.copy()[:, :320, :]
        right_bc = blend_color.copy()[:, 320:, :]

        left_binary = self.binary_image(left_bc)
        right_binary = self.binary_image(right_bc)

        self.lx, self.ly, self.lflag, self.lcount = self.calculateMoment(left_binary)
        self.rx, self.ry, self.rflag, self.rcount = self.calculateMoment(right_binary)
        
        if self.rx == 0 :
            self.rx = 320

        print(f'({self.lx}, {self.ly}), ({self.rx},{self.ry})')
#         print(f'shape={right_binary.shape}, rx={self.rx}, ry={self.ry}, rflag={self.rflag}, rcount={self.rcount}')

#         cv2.circle(left_bc, (self.lx, self.ly), 3, (0, 255, 0), -1)
#         cv2.circle(right_bc, (self.rx, self.ry), 3, (0, 255, 0), -1)
        
#         cv2.namedWindow("left_bc", cv2.WINDOW_AUTOSIZE)
#         cv2.imshow("left_bc", left_bc)
#         cv2.namedWindow("right_bc", cv2.WINDOW_AUTOSIZE)
#         cv2.imshow("right_bc", right_bc)
#         cv2.waitKey(1)
                
if __name__ == '__main__':
    try:
        cr = cameraRec()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    except ZeroDivisionError:
        pass
        