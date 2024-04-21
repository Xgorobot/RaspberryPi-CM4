import math
import os
import socket
import sys
import time

import numpy as np
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
from xgolib import XGO

# ---------------------INIT------------------------ #
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width), "black")
display.ShowImage(splash)
button = Button()

import cv2

camera = cv2.VideoCapture(0)
camera.set(3, 320)
camera.set(4, 240)

dog = XGO(port='/dev/ttyAMA0', version="xgomini")

dog.attitude('p', 15)
dog.translation('z', 75)

fm = dog.read_firmware()
if fm[0] == 'M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0', version="xgomini")
    dog_type = 'M'
else:
    print('XGO-LITE')
    dog_type = 'L'

# ---------------------FOLLOW LINE------------------------ #
# pid
error = 0  # 当前误差e[k]
last_error = 0  # 上一次误差e[k-1]
pre_error = 0  # 上上次误差e[k-2]
proportion = 1  # 比例系数3 0.2
integral = 0.5  # 积分系数1.2
derivative = 0  # 微分系数1.2
 
stop_flag = 1
control_flag = 1
turn_speed = 30
speed = 30
back_speed = 30


width, height = 160, 120
 
 
def TrackBar_Init():
    # 1 create windows
    cv2.namedWindow('h_binary')
    cv2.namedWindow('s_binary')
    cv2.namedWindow('l_binary')
    # 2 Create Trackbar
    cv2.createTrackbar('hmin', 'h_binary', 0, 179, call_back)
    cv2.createTrackbar('hmax', 'h_binary', 110, 179, call_back)
    cv2.createTrackbar('smin', 's_binary', 0, 255, call_back)
    cv2.createTrackbar('smax', 's_binary', 51, 255, call_back)  # 51
    cv2.createTrackbar('lmin', 'l_binary', 0, 255, call_back)
    cv2.createTrackbar('lmax', 'l_binary', 255, 255, call_back)
    '''cv2.namedWindow('binary')
    cv2.createTrackbar('thresh', 'binary', 154, 255, call_back)  '''
    #   创建滑动条     滑动条值名称 窗口名称   滑动条值 滑动条阈值 回调函数
 

 
def Forward(turn_speed):
    dog.move('x',turn_speed)
 
 
def Back(turn_speed):
    dog.move('y',turn_speed)
 
 
def Left(turn_speed):
    dog.turn(turn_speed)
 
def Right(turn_speed):
    dog.turn(0-turn_speed)
 
 
def Stop():
    dog.stop()
 
def call_back(*arg):
    pass
 
# 在HSV色彩空间下得到二值图
def Get_HSV(image):
    # 界面控制
    # hmin = cv2.getTrackbarPos('hmin', 'h_binary')
    # hmax = cv2.getTrackbarPos('hmax', 'h_binary')
    # smin = cv2.getTrackbarPos('smin', 's_binary')
    # smax = cv2.getTrackbarPos('smax', 's_binary')
    # lmin = cv2.getTrackbarPos('lmin', 'l_binary')
    # lmax = cv2.getTrackbarPos('lmax', 'l_binary')
    hmin = 2
    hmax = 170
    smin = 10
    smax = 160
    lmin = 80
    lmax = 200
 
    # 2 to HSV
    hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    #cv2.imshow('hls', hls)
    h, l, s = cv2.split(hls)
 
    # 3 set threshold (binary image)
    # if value in (min, max):white; otherwise:black
    h_binary = cv2.inRange(np.array(h), np.array(hmin), np.array(hmax))
    s_binary = cv2.inRange(np.array(s), np.array(smin), np.array(smax))
    l_binary = cv2.inRange(np.array(l), np.array(lmin), np.array(lmax))
 
    # 4 get binary（对H、S、V三个通道分别与操作）
    binary = 255 - cv2.bitwise_and(h_binary, cv2.bitwise_and(s_binary, l_binary))
    # 5 Show
    #cv2.imshow('h_binary', h_binary)
    #cv2.imshow('s_binary', s_binary)
    #cv2.imshow('l_binary', l_binary)
    #cv2.imshow('binary', binary)
 
    return binary
 
# 图像处理
def Image_Processing():
    global frame, binary
    # Capture the frames
    ret, frame = camera.read()
 
    # to binary
    binary = Get_HSV(frame)
 
    blur = cv2.GaussianBlur(binary, (5, 5), 0)
    #cv2.imshow('blur', blur)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35))
    Open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    #cv2.imshow('Open', Open)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    Erode = cv2.morphologyEx(Open, cv2.MORPH_ERODE, kernel)
    #cv2.imshow('Erode', Erode)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    Dilate = cv2.morphologyEx(Erode, cv2.MORPH_DILATE, kernel)
    #cv2.imshow('Dilate', Dilate)
    binary = Erode  # Dilate
 
# 找线
def Find_Line():
    global x, y, image
    # 1 找出所有轮廓
    contours, hierarchy = cv2.findContours(binary, 1, cv2.CHAIN_APPROX_NONE)
 
    # 2 找出最大轮廓
    if len(contours) > 0:
        # 最大轮廓
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
 
        # 中心点坐标
        x = int(M['m10'] / M['m00'])
        y = int(M['m01'] / M['m00'])
        # print(x, y)
 
        # 显示
        image = frame.copy()
        # 标出中心位置
        cv2.line(image, (x, 0), (x, 320), (0, 0, 255), 1)
        cv2.line(image, (0, y), (320, y), (0, 0, 255), 1)
        # 画出轮廓
        cv2.drawContours(image, contours, -1, (128, 0, 128), 2)
        #cv2.imshow("image", image)
        b, g, r1 = cv2.split(image)
        image = cv2.merge((r1, g, b))
        imgok = Image.fromarray(image)
        display.ShowImage(imgok)
 
    else:
        print("not found the line")
 
        (x, y) = (0, 0)
 
 
def Pid():
    global turn_speed, x, y, speed
    global error, last_error, pre_error, out_pid
 
    error = abs(x - width / 2)
 
    out_pid = int(proportion * error - integral * last_error + derivative * pre_error)
    turn_speed = out_pid
 
    # 保存本次误差，以便下一次运算
    pre_error = last_error
    last_error = error
 
    # 限值
    if (turn_speed < 30):
        turn_speed = 30
    elif (turn_speed > 100):
        turn_speed = 100
    if (speed < 0):
        speed = 0
    elif (speed > 100):
        speed = 100
 
    print(error, out_pid, turn_speed, (x, y))
 
# 巡线
def Follow_Line():
    global turn_speed, x, y, speed, back_speed
 
    '''if(x < width / 2 and y>2*height/3):
        Left(turn_speed)
    elif(x>3*width/2 and y>2*height/3):
        Right(turn_speed)'''
    if (0 < x < width / 4):
        Left(turn_speed)
        print("turn left")
    elif (3 * width / 4 < x < width):
        Right(turn_speed)
        print("turn right")
    # 直角拐弯
    elif (y > 3 * height / 4):
        if (x < width / 2):
            Left(turn_speed * 2)
            print("turn left")
        elif (x >= width / 2):
            Right(turn_speed * 2)
            print("turn right")
    elif (x >= width / 4 and x <= 3 * width / 4):
        Forward(speed)
 
    elif (x == 0 and y == 0):
        Back(back_speed)



#TrackBar_Init()
while True:
    Image_Processing()
    Find_Line()
    Pid()
    if cv2.waitKey(1) == ord('q'):
        cv2.destroyAllWindows()
        break
    
dog.reset()
camera.release()
cv2.destroyAllWindows()
sys.exit()
 
 