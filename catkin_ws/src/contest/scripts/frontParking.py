#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import rospy
from std_msgs.msg import Float32MultiArray
from jetracer.nvidia_racecar import NvidiaRacecar
from smarp_msgs.msg import objectStatus, lidarStatus, objInfo, camInfo

class ParallelParking:
    def __init__(self):
        self.car = NvidiaRacecar()
        rospy.init_node('ultrasonic_subscriber')
        self.distances = [0, 0, 0, 0]  # [오른쪽, 왼쪽, 뒤쪽, 앞쪽] 순서
        self.state = 0  # 초기 상태는 대기 (0)

        self.car.throttle = 0
        self.left_detect = 0
        rospy.Subscriber('/distance', Float32MultiArray, self.distance_callback)
        
        rospy.spin()
        
        
    def jet_Control(self, steer, speed) :
        self.car.throttle = speed/1000
        # self.car.throttle = 0
        self.car.steering = steer


    def distance_callback(self, msg):
        self.distances = msg.data
        rospy.loginfo(f"Received distances: "
                      f"Front: {self.distances[3]:.2f} cm, "
                      f"Rear: {self.distances[2]:.2f} cm, "
                      f"Left: {self.distances[1]:.2f} cm, "
                      f"Right: {self.distances[0]:.2f} cm,"
                    )

            

        self.jet_Control(-1.0,-210)

        if self.distances[2] <= 10:
            self.jet_Control(0.0, 0.0)
        self.left_detect = 0
        print(self.left_detect)



if __name__ == '__main__':
    try:
        ParallelParking()
    except rospy.ROSInterruptException:
        pass