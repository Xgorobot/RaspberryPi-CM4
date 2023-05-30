import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
from xgolib import XGO
import threading

exit_mark=False
acting=False
x=y=r=0
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
fm=dog.read_firmware()
if fm[0]=='M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0',version="xgomini")
    dog_type='M'
else:
    print('XGO-LITE')
    dog_type='L'
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()
width, height = 320, 240
camera = cv2.VideoCapture(0)
camera.set(3,width) 
camera.set(4,height) 


dog.reset()
time.sleep(1)
if dog_type=='L':
    dog.attitude('p',99)
    time.sleep(1)
    dog.translation('z',70)
elif dog_type=='M':
    dog.attitude('p',100)
    time.sleep(1)
    dog.translation('z',100)

  
def Front(speed,tim):
    global acting
    acting=True
    dog.move('x',speed)
    time.sleep(tim)
    dog.stop()
    time.sleep(0.1)
    acting=False
    
def Back(speed):
    global acting
    acting=True
    dog.move('x',0-speed)
    time.sleep(0.7)
    dog.stop()
    time.sleep(0.1)
    acting=False
 
def Left(speed):
    global acting
    acting=True
    dog.turn(speed)
    time.sleep(1.1)
    dog.stop()
    time.sleep(0.2)
    acting=False

def Right(speed):
    global acting
    acting=True
    dog.turn(0-speed)
    time.sleep(1.1)
    dog.stop()
    time.sleep(0.2)
    acting=False
 
def Stop():
    global acting
    if acting==False:
        dog.turn(0)
        dog.move('x',0)

 
def Image_Processing():
    global h,s,v,x,y,r,acting
    ret, frame = camera.read()
    image = frame
    x=y=r=0
    gray_img= cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    img = cv2.medianBlur(gray_img,5)
    circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT,1,20,param1=100,param2=35,minRadius=10,maxRadius=66)
    if acting==False:
        if circles is not None:
            x, y, r = int(circles[0][0][0]),int(circles[0][0][1]),int(circles[0][0][2])
            #print(x,y,r)
            cv2.circle(image, (x, y), r, (255,0,255),5)
        else:
            (x,y),r = (0,0), 0
    b,g,r1 = cv2.split(image)
    image = cv2.merge((r1,g,b))
    image = cv2.flip(image, 1)
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)
    if x!=0 and y!=0 and r!=0:
        print(x,y,r)
 

def dog_move(threadName):
    global x,y,r,acting,exit_mark
    while exit_mark==False:
        if r>48:
            Back(5)
        elif r>=43:
            print('bingo')
            acting=True
            dog.action(130)
            time.sleep(10)
            dog.claw(0)
            time.sleep(1)
            dog.reset()
            time.sleep(1)
            dog.attitude('p',99)
            time.sleep(1)
            dog.translation('z',70)
            acting=False
                
        if acting==False:
            if x==0:
                Stop()
            elif x<135:
                print('left')
                Left(10)
            elif x>185:
                print('right')
                Right(11)
            else:
                print('middle')
                if 10<r and r<25:
                    print('big step')
                    Front(35,0.9)
                elif r<34:
                    print('small step')
                    Front(10,0.8)

def dog_move_m(threadName):
    global x,y,r,acting,exit_mark
    while exit_mark==False:
        if r>60:
            Back(5)
        elif r>=51:
            print('bingo')
            acting=True
            dog.action(130)
            time.sleep(10)
            dog.claw(0)
            time.sleep(1)
            dog.reset()
            time.sleep(1)
            dog.attitude('p',100)
            time.sleep(1)
            dog.translation('z',100)
            acting=False
                
        if acting==False:
            if x==0:
                Stop()
            elif x<135:
                print('left')
                Left(9)
            elif x>185:
                print('right')
                Right(9)
            else:
                print('middle')
                if 10<r and r<33:
                    print('big step')
                    Front(16,0.8)
                elif r<34:
                    print('small step')
                    Front(7,0.6)

if dog_type=='L':
    moving = threading.Thread(target=dog_move, args=("Thread-1",))
    moving.start()
elif dog_type=='M':
    moving = threading.Thread(target=dog_move_m, args=("Thread-1",))
    moving.start()

while 1:
    Image_Processing()
    if button.press_b():
        dog.reset()
        exit_mark=True
        break  
    if button.press_a():
        dog.reset()
        dog.action(130)


