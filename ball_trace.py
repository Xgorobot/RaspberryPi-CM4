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

red=(255,0,0)
green=(0,255,0)
blue=(0,0,255)
yellow=(255,255,0)

color_lower = np.array([0, 43, 46])
color_upper = np.array([10, 255, 255])
g_mode=1
cm=1
mode=1
  
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
    
def change_color():
    global color_lower,color_upper,mode
    if mode==4:
        mode=1
    else:
        mode+=1
    if mode==1:
        color_lower = np.array([0, 43, 46])
        color_upper = np.array([10, 255, 255])
    elif mode==2:
        color_lower = np.array([35, 43, 46])
        color_upper = np.array([77, 255, 255])
    elif mode==3:
        color_lower = np.array([35, 43, 46])
        color_upper = np.array([77, 255, 255])
    elif mode==4:
        color_lower = np.array([35, 43, 46])
        color_upper = np.array([77, 255, 255])
 
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
    ret, frame = camera.read()
    image = frame
    binary = Get_HSV(frame)
    blur = cv2.GaussianBlur(binary,(9,9),0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    Open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    Close = cv2.morphologyEx(Open, cv2.MORPH_CLOSE, kernel)
    circles = cv2.HoughCircles(Close,cv2.HOUGH_GRADIENT,2,120,param1=120,param2=50,minRadius=20,maxRadius=0)
    if circles is not None:
        x, y, r = int(circles[0][0][0]),int(circles[0][0][1]),int(circles[0][0][2])
        print(x, y, r)
        cv2.circle(image, (x, y), r, (255,0,255),5)
    else:
        (x,y),r = (0,0), 0
    b,g,r = cv2.split(image)
    image = cv2.merge((r,g,b))
    image = cv2.flip(image, 1)
    if mode==1:
        cv2.rectangle(image, (290, 10), (320, 40), red, -1)
    elif mode==2:
        cv2.rectangle(image, (290, 10), (320, 40), green, -1)
    elif mode==3:
        cv2.rectangle(image, (290, 10), (320, 40), blue, -1)
    elif mode==4:
        cv2.rectangle(image, (290, 10), (320, 40), yellow, -1)
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)
    return (x,y), r
 
def Move(t, r):
    (x,y)=t
    low_xlimit = 0.4*width
    high_xlimit = 0.6 * width
    ylimit = 0.5 * height
    print(high_xlimit, ylimit)
    if x==0:
        Stop()
    elif x>low_xlimit and x<high_xlimit and y<ylimit:
        Front(5)
    elif x>low_xlimit and x<high_xlimit and y>=ylimit:
        Back(5)
    elif x<low_xlimit:
        Left(5)
    elif x>high_xlimit:
        Right(5)
 
    
while 1:
    (x,y), r = Image_Processing()
    Move((x,y), r)
    if button.press_d():
        change_color()
    if button.press_b():
        break  
