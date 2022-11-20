import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# For each person, enter one numeric face id
face_id = input('\n enter user id end press <return> ==>  ')

print("\n [INFO] Initializing face capture. Look the camera and wait ...")
# Initialize individual sampling face count
count = 0

while 1:
    ret, img = cap.read() 
    if ret:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:

            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
            count += 1
            print(count)

            # Save the captured image into the datasets folder
            cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
            b,g,r = cv2.split(img)
            img = cv2.merge((r,g,b))
            imgok = Image.fromarray(img)
            display.ShowImage(imgok)
            #cv2.imshow('image', img)

            if button.press_b():
                break
            if count >= 30:
                print('done')
                break
    if count>=30:
        break
    if button.press_b():
        break


print("\n [INFO] Exiting Program and cleanup stuff")
cap.release()
cv2.destroyAllWindows() 


