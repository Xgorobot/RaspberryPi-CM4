import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0',version="xgolite")
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()
width, height = 320, 240
camera = cv2.VideoCapture(0)
camera.set(3,width) 
camera.set(4,height) 
  
def Front(speed):
    dog.move('x',speed)
    
def Back(speed):
    dog.move('x',0-speed)
 
def Left(speed):
    dog.turn(speed)
 
def Right(speed):
    dog.turn(0-speed)
 
def Stop():
    dog.reset()
   
def nothing(*arg):
    pass
 
def Get_HSV(image):
    hmin = 1
    hmax = 200
    smin = 110
    smax = 255
    vmin = 140
    vmax = 255
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    h_binary = cv2.inRange(np.array(h), np.array(hmin), np.array(hmax))
    s_binary = cv2.inRange(np.array(s), np.array(smin), np.array(smax))
    v_binary = cv2.inRange(np.array(v), np.array(vmin), np.array(vmax))
    binary = cv2.bitwise_and(h_binary, cv2.bitwise_and(s_binary, v_binary))
    return binary
 
def Image_Processing():
    global h, s, v
    # 1 Capture the frames
    ret, frame = camera.read()
    image = frame
    #cv2.imshow('frame', frame)
    
    # 2 get HSV
    binary = Get_HSV(frame)
    
    # 3 Gausi blur
    blur = cv2.GaussianBlur(binary,(9,9),0)
    
    # 4 Open
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    Open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    # 5 Close
    Close = cv2.morphologyEx(Open, cv2.MORPH_CLOSE, kernel)
    # 6 Hough Circle detect
    circles = cv2.HoughCircles(Close,cv2.HOUGH_GRADIENT,2,120,param1=120,param2=50,minRadius=20,maxRadius=0)
    #                                                                     
    # judge if circles is exist
    if circles is not None:
        x, y, r = int(circles[0][0][0]),int(circles[0][0][1]),int(circles[0][0][2])
        print(x, y, r)
        cv2.circle(image, (x, y), r, (255,0,255),5)
        #cv2.imshow('image', image)
    else:
        (x,y),r = (0,0), 0
    b,g,r = cv2.split(image)
    image = cv2.merge((r,g,b))
    image = cv2.flip(image, 1)
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)
    return (x,y), r
 
 
# 运动控制（这里可以做到跟踪小球，前景和后退相配合，“敌进我退，敌退我进”）
def Move(t, r):
    (x,y)=t
    low_xlimit = 0.4*width
    high_xlimit = 0.6 * width
    #low_ylimit = 3/4 * height
    ylimit = 0.5 * height
    print(high_xlimit, ylimit)
    # 没检测到，停止不动
    if x==0:
        Stop()
    # 检测到在图片0.75以上的区域（距离正常）
    elif x>low_xlimit and x<high_xlimit and y<ylimit:
        Front(5)
    # 检测到在图片0.75以下的区域（距离过近，后退）
    elif x>low_xlimit and x<high_xlimit and y>=ylimit:
        Back(5)
    # 在左0.25区域，向左跟踪
    elif x<low_xlimit:
        Left(5)
    # 在右0.25区域，向右跟踪
    elif x>high_xlimit:
        Right(5)
 
    
while 1:
    (x,y), r = Image_Processing()
    Move((x,y), r)
    if button.press_b():
        break  
