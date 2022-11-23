import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import mediapipe as mp
from numpy import linalg
from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")


display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

color_lower = np.array([156, 43, 46])
color_upper = np.array([180, 255, 255])
g_mode=1
'''
elif b.description == Name_widgets['Red'][g_ENABLE_CHINESE]:
color_lower = np.array([0, 43, 46])
color_upper = np.array([10, 255, 255])
g_dog.action(0xff)
g_mode = 1
elif b.description == Name_widgets['Green'][g_ENABLE_CHINESE]:
color_lower = np.array([35, 43, 46])
color_upper = np.array([77, 255, 255])
g_dog.action(0xff)
g_mode = 1
elif b.description == Name_widgets['Blue'][g_ENABLE_CHINESE]:
color_lower=np.array([100, 43, 46])
color_upper = np.array([124, 255, 255])
g_dog.action(0xff)
g_mode = 1
elif b.description == Name_widgets['Yellow'][g_ENABLE_CHINESE]:
color_lower = np.array([26, 43, 46])
color_upper = np.array([34, 255, 255])
g_dog.action(0xff)
'''

#-----------------------COMMON INIT-----------------------
font = cv2.FONT_HERSHEY_SIMPLEX 
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")

    
    
    
global color_lower, color_upper, g_mode
t_start = time.time()
fps = 0
color_x = 0
color_y = 0
color_radius = 0
while 1:
    ret, frame = cap.read()
    frame_ = cv2.GaussianBlur(frame,(5,5),0)                    
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,color_lower,color_upper)  
    mask = cv2.erode(mask,None,iterations=2)
    mask = cv2.dilate(mask,None,iterations=2)
    mask = cv2.GaussianBlur(mask,(3,3),0)     
    cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 
    if g_mode == 1: # 按钮切换开关  button switch
        if len(cnts) > 0:
            cnt = max (cnts, key = cv2.contourArea)
            (color_x,color_y),color_radius = cv2.minEnclosingCircle(cnt)
            if color_radius > 10:
                # 将检测到的颜色标记出来  Mark the detected color
                cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                value_x = color_x - 320
                value_y = color_y - 240
                if value_x > 110:
                    value_x = 110
                elif value_x < -110:
                    value_x = -110
                if value_y > 150:
                    value_y = 150
                elif value_y < -150:
                    value_y = -150
                g_dog.attitude(['y','p'],[-value_x/10, value_y/10])
        else:
            color_x = 0
            color_y = 0
        cv2.putText(frame, "X:%d, Y%d" % (int(color_x), int(color_y)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)
        t_start = time.time()
        fps = 0
    else:
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        cv2.putText(frame, "FPS " + str(int(mfps)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)

    
    b,g,r = cv2.split(frame)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break

cap.release()
cv2.destroyAllWindows() 