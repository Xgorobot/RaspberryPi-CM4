import numpy as np
import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

width, height = 320, 240
camera = cv2.VideoCapture(0)
camera.set(3,width) 
camera.set(4,height) 
 
def nothing(*arg):
    pass
 
 
 
# 图像处理
def Image_Processing():
    global h, s, v
    # 1 Capture the frames
    ret, frame = camera.read()
    image = frame
    cv2.imshow('frame', frame)
    
    # 2 get HSV
    binary = Get_HSV(frame)
    
    # 3 Gausi blur
    blur = cv2.GaussianBlur(binary,(9,9),0)
    
    # 4 Open
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    Open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    #cv2.imshow('Open',Open)
    # 5 Close
    Close = cv2.morphologyEx(Open, cv2.MORPH_CLOSE, kernel)
    #cv2.imshow('Close',Close)
 
    # 6 Hough Circle detect
    circles = cv2.HoughCircles(Close,cv2.HOUGH_GRADIENT,2,120,param1=120,param2=20,minRadius=20,maxRadius=0)
    #                                                                     param2:决定圆能否被检测到（越少越容易检测到圆，但相应的也更容易出错）
    # judge if circles is exist
    if circles is not None:
        # 1 获取圆的圆心和半径
        x, y, r = int(circles[0][0][0]),int(circles[0][0][1]),int(circles[0][0][2])
        print(x, y, r)
        # 2 画圆
        cv2.circle(image, (x, y), r, (255,0,255),5)
        #cv2.imshow('image', image)
    else:
        (x,y),r = (0,0), 0
    b,g,r = cv2.split(image)
    image = cv2.merge((r,g,b))
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)    
    return (x,y), r
 
 
# 运动控制（这里可以做到跟踪小球，前景和后退相配合，“敌进我退，敌退我进”）
def Move():
    pass
#     low_xlimit = width/4
#     high_xlimit = 0.75 * width
#     #low_ylimit = 3/4 * height
#     ylimit = 0.75 * height
#     print(high_xlimit, ylimit)
#     # 没检测到，停止不动
#     if x==0:
#         Stop()
#     # 检测到在图片0.75以上的区域（距离正常）
#     elif x>low_xlimit and x<high_xlimit and y<ylimit:
#         Front(60)
#     # 检测到在图片0.75以下的区域（距离过近，后退）
#     elif x>low_xlimit and x<high_xlimit and y>=ylimit:
#         Back(60)
#     # 在左0.25区域，向左跟踪
#     elif x<low_xlimit:
#         Left(60)
#     # 在右0.25区域，向右跟踪
#     elif x>high_xlimit:
#         Right(60)
 
    
if __name__ == '__main__':
    while 1:
        (x,y), r = Image_Processing()
        #Move()
        if button.press_b():
          break