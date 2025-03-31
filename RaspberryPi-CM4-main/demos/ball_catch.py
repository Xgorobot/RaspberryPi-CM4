import math
import os
import socket
import sys
import time

import numpy as np
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
from xgolib import XGO

# ---------------------INIT------------------------ #
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width), "black")
display.ShowImage(splash)
button = Button()

import cv2

camera = cv2.VideoCapture(0)
camera.set(3, 320)
camera.set(4, 240)

dog = XGO(port='/dev/ttyAMA0', version="xgomini")

fm = dog.read_firmware()
if fm[0] == 'M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0', version="xgomini")
    dog_type = 'M'
else:
    print('XGO-LITE')
    dog_type = 'L'

# ---------------------MAIN------------------------ #
CircleCount = 0
mx = 0
my = 0
mr = 0
distance = 0
yaw_err = 0
if dog_type == 'L':
    mintime_yaw = 0.8
    mintime_x = 0.1
else:
    mintime_yaw = 0.7
    mintime_x = 0.3
def Image_Processing():
    global CircleCount, mx, my, mr, distance, yaw_err
    ret, image = camera.read()
    x, y, r = 0, 0, 0
    image = cv2.GaussianBlur(image, (3, 3), 0)
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 30, param1=64, param2=32, minRadius=6, maxRadius=35)

    if circles is not None:
        if len(circles[0]) == 1:
            ball = circles[0][0]
            x, y, r = int(ball[0]), int(ball[1]), int(ball[2])
            cv2.circle(image, (x, y), r, (0, 0, 255), 2)
            cv2.circle(image, (x, y), 2, (0, 0, 255), 2)
            print("x:{}, y:{}, r:{}".format(x, y, r))
            CircleCount += 1
            mx = (CircleCount - 1) * mx / CircleCount + x / CircleCount
            my = (CircleCount - 1) * my / CircleCount + y / CircleCount
            mr = (CircleCount - 1) * mr / CircleCount + r / CircleCount

    if CircleCount >= 15:
        CircleCount = 0
        distance = 0.07 * mr * mr - 3.435 * r + 54.82
        yaw_err = -(mx - 160) / distance
        turn_time = abs(yaw_err) / 9 + mintime_yaw
        run_time = distance / 10.5 + mintime_x
        if distance > 25:
            dog.move_x(10)
            time.sleep(1.6)
            dog.move_x(0)
            return
        if yaw_err > 4/distance:
            dog.turn(25)
            time.sleep(turn_time)
            dog.turn(0)
        elif yaw_err < -4/distance:
            dog.turn(-25)
            time.sleep(turn_time)
            dog.turn(0)
        else:
            dog.move_x(10)
            time.sleep(run_time)
            dog.move_x(0)
            dog.action(0x82)
            time.sleep(9)
            dog.attitude('p', 15)
            dog.translation('z', 75)

    cv2.putText(image, "x:" + format(mx, ".1f"), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, "y:" + format(my, ".1f"), (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, "r:" + format(mr, ".1f"), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, "d:" + format(distance, ".1f"), (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, "e:" + format(yaw_err, ".1f"), (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    b, g, r1 = cv2.split(image)
    image = cv2.merge((r1, g, b))
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)


dog.attitude('p', 15)
dog.translation('z', 75)
while camera.isOpened():
    if button.press_b():
        dog.reset()
        camera.release()
        cv2.destroyAllWindows()
        sys.exit()
    Image_Processing()

