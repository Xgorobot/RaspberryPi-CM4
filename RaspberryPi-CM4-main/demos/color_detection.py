import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np



display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")   
display.ShowImage(splash)
button=Button()



# color red, green, blue, yellow
color_list = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]

color_lower_list = [np.array([0, 43, 46]),
                    np.array([45, 43, 46]),
                    np.array([100, 43, 46]),
                    np.array([26, 43, 46]),
                    ]
                    
color_upper_list = [np.array([10, 255, 255]),
                    np.array([65, 255, 255]),
                    np.array([124, 255, 255]),
                    np.array([34, 255, 255]),
                    ]


# detect range
detection_x_lower = 80
detection_x_upper = 240
detection_y_lower = 60
detection_y_upper = 180

buffer = 30

#-----------------------COMMON INIT-----------------------
font = cv2.FONT_HERSHEY_SIMPLEX 
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")


while 1:
    ret, frame = cap.read()
    frame_ = cv2.GaussianBlur(frame,(5,5),0)                    
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    color_show_index = -1
    color_radius_pre = 0
    color_x_pre = 0
    color_y_pre = 0
    for color_index in range(0, len(color_list)):
        color_lower = color_lower_list[color_index]
        color_upper = color_upper_list[color_index]
        mask = cv2.inRange(hsv,color_lower,color_upper)  
        mask = cv2.erode(mask,None,iterations=2)
        mask = cv2.dilate(mask,None,iterations=2)
        mask = cv2.GaussianBlur(mask,(3,3),0)     
        cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 

        if len(cnts) > 0:
            for cnt in cnts:
                (color_x,color_y),color_radius = cv2.minEnclosingCircle(cnt)
                if (color_radius > 10 
                    and color_radius > color_radius_pre
                    and color_x < detection_x_upper             # 检测中心点在矩阵内
                    and color_x > detection_x_lower 
                    and color_y < detection_y_upper 
                    and color_y > detection_y_lower
                    and color_x + color_radius < detection_x_upper + buffer     # 检测范围不超过buffer
                    and color_x - color_radius > detection_x_lower - buffer
                    and color_y + color_radius < detection_y_upper + buffer
                    and color_y - color_radius > detection_y_lower - buffer
                    ):
                    color_radius_pre = color_radius
                    color_x_pre = color_x
                    color_y_pre = color_y
                    color_show_index = color_index
   
    frame = cv2.flip(frame, 1)  # 翻转
    b,g,r = cv2.split(frame)
    img = cv2.merge((r,g,b))
    cv2.putText(img, "X:%d, Y%d" % (int(color_x_pre), int(color_y_pre)), (40,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 3)
    cv2.rectangle(img, (detection_x_lower, detection_y_lower), (detection_x_upper, detection_y_upper), (255,255,255), 1)
    if color_show_index != -1:
        cv2.circle(img,(320-int(color_x_pre),int(color_y_pre)),int(color_radius_pre),color_list[color_show_index],2)  

    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break

cap.release()
cv2.destroyAllWindows() 
