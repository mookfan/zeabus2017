#!/usr/bin/env python
import cv2
import numpy as np
import rospkg
import rospy
import math
from sensor_msgs.msg import CompressedImage
from vision_lib import *
from zeabus_vision_srv_msg.msg import vision_msg_default
from zeabus_vision_srv_msg.srv import vision_srv_default

img = None

lower_red = np.array([ 0, 15, 73])
upper_red = np.array([92, 172, 136])

def find_path():
    global img
    t = True
    f = False
    cnt = None
    kernel1 = np.ones((9,9), np.uint8)
    kernel2 = np.ones((5,5), np.uint8)
    res = vision_msg_default()

    while not rospy.is_shutdown():
        while img is None:
            print("img: None")
        im = img.copy()
        area = -999
        max1 = -999
        cx = -999
        cy = -999
        w = -999
        h = -999
        angle = -999
        box = None
        imStretching = stretching(im)
        im_for_draw = img.copy()
        im_blur = cv2.GaussianBlur(im, (3,3), 0)
        hsv = cv2.cvtColor(im_blur, cv2.COLOR_BGR2HSV)
        # hsv2 = cv2.cvtColor(im_blur, cv2.COLOR_RGB2HSV)
        imgray = cv2.cvtColor(im_blur, cv2.COLOR_BGR2GRAY)
        im_red = cv2.inRange(hsv, lower_red, upper_red)
        dilation = cv2.dilate(im_red, kernel1, iterations =  1)
        erosion = cv2.erode(dilation, kernel2, iterations = 1)
        ret, thresh = cv2.threshold(imgray, 200, 255, 0)
        # thresh = cv2.adaptiveThreshold(imgray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 195, 1)
        _, contours, hierarchy = cv2.findContours(dilation.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            M = cv2.moments(c)
            # x,y,w,h = cv2.boundingRect(c)
            # cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0) ,2)
            rect = (x,y),(ww,hh),angle1 =cv2.minAreaRect(c)
            area = ww*hh

            if area < 5500:
                continue
            if hh == 0 :
                continue
            print(hh)


            # if hh < 170:
            #     continue

            if ww > hh:
                tmp = hh
                hh = ww
                ww = tmp

            diff = (ww/hh)
            if diff > 0.3:
                continue
            epsilon = 0.1*cv2.arcLength(c, t)
            approx = cv2.approxPolyDP(c, epsilon,t)
            
            if area > max1:
                max1 = area
                # cnt = c
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                angle = 90-Oreintation(M)[0]*180/math.pi
                cx = x
                cy = y
                w = ww
                h = hh
            # cv2.drawContours(im_for_draw,[box], -1,(0,0,255),1)
            cv2.drawContours(im, [approx], 0, (0, 0, 255), 2)

        print('w', w)
        print('h', h)

        res.area = area
        if area < 4000:
            res.appear = False
            res.area = -999
            res.angle = -999
            res.x = -999
            res.y = -999
            return res
        else:
            res.appear = True
            res.area = area
            res.angle = angle
            res.x = (cx-400)/400
            res.y = (300-cy)/300
            return res


        cv2.circle(im_for_draw,(int(cx), int(cy)), 5, (0, 0, 255), -1)
        cv2.drawContours(im_for_draw,[box], -1,(0,0,255),1)
        cv2.drawContours(im, contours, -1, (0,255,0), 3)
        # cv2.imshow('grey', imgray)
        # cv2.imshow('thresh', thresh)
        # cv2.imshow('red', im_red)
        # cv2.imshow('dilation', dilation)
        # cv2.imshow('erode', erosion)
        # cv2.imshow('img_blur',im_blur)
        cv2.imshow('img',im_for_draw)
        cv2.imshow('img1',im)
        # cv2.imshow('hsv', hsv)
        # cv2.imshow('hsv from bgr', hsv)
        # cv2.imshow('img stretching', imStretching)
        cv2.waitKey(30)


def img_callback(msg):
    global img

    arr = np.fromstring(msg.data, np.uint8)
    img = cv2.imdecode(arr, 1)

def mission_callback(msg):
    return findPath()

if __name__ == '__main__':
    rospy.init_node('findPath')
    topic = '/leftcam_bottom/image_raw/compressed'
    rospy.Subscriber(topic, CompressedImage, img_callback)
    rospy.Service('vision', vision_srv_default, mission_callback)
    rospy.spin()