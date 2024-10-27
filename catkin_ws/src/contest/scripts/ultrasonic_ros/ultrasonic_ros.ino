#define TRIG1 11  //right
#define ECHO1 10

#define TRIG2 9   //left
#define ECHO2 8

#define TRIG3 7   // back
#define ECHO3 6

#define TRIG4 5 // front
#define ECHO4 4

#include <ros.h>
#include <std_msgs/Float32MultiArray.h>

ros::NodeHandle nh;
std_msgs::Float32MultiArray distance_msg;
ros::Publisher distancePublisher("/distance", &distance_msg);

void setup()
{
  nh.initNode();
  nh.advertise(distancePublisher);
  Serial.begin(9600);
  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);
  pinMode(TRIG3, OUTPUT);
  pinMode(ECHO3, INPUT);
  pinMode(TRIG4, OUTPUT);
  pinMode(ECHO4, INPUT);

  distance_msg.data_length = 4; 
  distance_msg.data = (float*)malloc(sizeof(float) * 4); 
}

float getDistance(int trigPin, int echoPin) {
  float duration, distance;
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2; 
  return distance;
}

void loop()
{
  distance_msg.data[0] = getDistance(TRIG1, ECHO1);
  distance_msg.data[1] = getDistance(TRIG2, ECHO2);
  distance_msg.data[2] = getDistance(TRIG3, ECHO3);
  distance_msg.data[3] = getDistance(TRIG4, ECHO4);

  // Serial.print("Distance1: ");
  // Serial.print(distance_msg.data[0]);
  // Serial.println(" cm");
  
  // Serial.print("Distance2: ");
  // Serial.print(distance_msg.data[1]);
  // Serial.println(" cm");
  
  // Serial.print("Distance3: ");
  // Serial.print(distance_msg.data[2]);
  // Serial.println(" cm");
  
  // Serial.print("Distance4: ");
  // Serial.print(distance_msg.data[3]);
  // Serial.println(" cm");
  
  distancePublisher.publish(&distance_msg);
  nh.spinOnce();
  delay(100);
}
