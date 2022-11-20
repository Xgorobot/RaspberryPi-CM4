import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import handtracking as htm
from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()
 
cap = cv2.VideoCapture(0) 
cap.set(3, 320) 
cap.set(4, 240)
length=0
 
while True:
    success, img = cap.read()
    img, lmList ,length= htm.handDetector(img) 
    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    #print(length)
    if length!=0:
        if length>1000:
            length=1000
        h=length/1000*40
        dog.translation('z', 75+h)
    else:
        dog.translation('z',95)
    if button.press_b():
        dog.reset()
        break

 
cap.release()
cv2.destroyAllWindows()