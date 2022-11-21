import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np

#define colors
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
button=Button()

font = ImageFont.truetype("msyh.ttc",22)
font2 = ImageFont.truetype("msyh.ttc",42)

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

count=0
# For each person, enter one numeric face id
face_id = input('\n enter user id end press <return> ==>  ')



while(True):

    ret, img = cap.read()
    if ret:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.1, 3)

        for (x,y,w,h) in faces:

            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
            count += 1

            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
            print(count)
            b,g,r = cv2.split(img)
            img = cv2.merge((r,g,b))
            imgok = Image.fromarray(img)
            display.ShowImage(imgok)

            #cv2.imshow('image', img)


        if count >= 30: # Take 30 face sample and stop video
             break
            

print("\n [INFO] Exiting Program and cleanup stuff")
cap.release()    
cv2.destroyAllWindows()



