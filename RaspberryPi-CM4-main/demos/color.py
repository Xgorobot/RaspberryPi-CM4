import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import mediapipe as mp
from numpy import linalg
from xgolib import XGO
g_dog = XGO(port='/dev/ttyAMA0',version="xgolite")
fm=g_dog.read_firmware()
if fm[0]=='M':
    print('XGO-MINI')
    g_dog = XGO(port='/dev/ttyAMA0',version="xgomini")
    dog_type='M'
elif fm[0]=='L':
    print('XGO-LITE')
    dog_type='L'
elif fm[0]=='R':
    print('XGO-RIDER')
    g_dog = XGO(port='/dev/ttyAMA0',version="xgorider")
    dog_type='R'
g_dog.reset()

red=(255,0,0)
green=(0,255,0)
blue=(0,0,255)
yellow=(255,255,0)
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")   
display.ShowImage(splash)
button=Button()

color_lower = np.array([0, 43, 46])
color_upper = np.array([10, 255, 255])
g_mode=1
cm=1
mode=1

def change_color():
    global color_lower,color_upper,mode
    if mode==4:
        mode=1
    else:
        mode+=1
    if mode==1:  #red
        color_lower = np.array([0, 43, 46])
        color_upper = np.array([10, 255, 255])
    elif mode==2: #green
        color_lower = np.array([35, 43, 46])
        color_upper = np.array([77, 255, 255])
    elif mode==3:   #blue
        color_lower = np.array([100, 43, 46])
        color_upper = np.array([124, 255, 255])
    elif mode==4:   #yellow
        color_lower = np.array([26, 43, 46])
        color_upper = np.array([34, 255, 255])


#-----------------------COMMON INIT-----------------------
font = cv2.FONT_HERSHEY_SIMPLEX 
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")

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
    if g_mode == 1:
        if len(cnts) > 0:
            cnt = max (cnts, key = cv2.contourArea)
            (color_x,color_y),color_radius = cv2.minEnclosingCircle(cnt)
            if color_radius > 10:
                cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                value_x = color_x - 160
                value_y = color_y - 120
                rider_x=value_x
                if value_x > 55:
                    value_x = 55
                elif value_x < -55:
                    value_x = -55
                if value_y > 75:
                    value_y = 75
                elif value_y < -75:
                    value_y = -75
                if dog_type=='L' or dog_type=='M':
                    g_dog.attitude(['y','p'],[-value_x/15, value_y/15])
                elif dog_type=='R':
                    print(color_y,75+int((190-color_y)/160*40))
                    g_dog.rider_height(75+int((190-color_y)/160*40))
                    if rider_x==9999:
                        g_dog.rider_turn(0)
                    else:
                        if rider_x > 35:
                            g_dog.rider_turn(-20)
                        elif rider_x < -35:
                            g_dog.rider_turn(20)
                        else:
                            g_dog.rider_turn(0)
        else:
            color_x = 0
            color_y = 0
            rider_x=9999
        cv2.putText(frame, "X:%d, Y%d" % (int(color_x), int(color_y)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)
        t_start = time.time()
        fps = 0
    else:
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        cv2.putText(frame, "FPS " + str(int(mfps)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)

    
    b,g,r = cv2.split(frame)
    img = cv2.merge((r,g,b))
    if mode==1:
        cv2.rectangle(img, (290, 10), (320, 40), red, -1)
    elif mode==2:
        cv2.rectangle(img, (290, 10), (320, 40), green, -1)
    elif mode==3:
        cv2.rectangle(img, (290, 10), (320, 40), blue, -1)
    elif mode==4:
        cv2.rectangle(img, (290, 10), (320, 40), yellow, -1)
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break
    if button.press_d():
        change_color()

cap.release()
