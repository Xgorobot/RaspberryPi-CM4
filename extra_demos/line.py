from line_common import *
import cv2
import cv2 as cv
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import mediapipe as mp
from numpy import linalg
from xgolib import XGO
import threading

red=(255,0,0)
green=(0,255,0)
blue=(0,0,255)
yellow=(255,255,0)
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")   
display.ShowImage(splash)
button=Button()

class LineDetect:
    def __init__(self):
        self.img = None
        self.circle = ()
        self.Roi_init = ()
        self.scale = 1000
        list=(0,43,46,10,255,255)
        self.hsv_text=((int(list[0]), int(list[1]), int(list[2])), (int(list[3]), int(list[4]), int(list[5])))
        self.hsv_range = self.hsv_text
        self.dyn_update = True

        self.select_flags = False
        self.Track_state = 'identify'
        self.windows_name = 'frame'
        self.color = color_follow()
        self.cols, self.rows = 0, 0
        self.FollowLinePID = (50, 0, 30)
        self.PID_init()
        self.dog = XGO(port='/dev/ttyAMA0',version="xgolite")
        self.dog_init()

    def execute(self, point_x, point_y, radius):
        [z_Pid, _] = self.PID_controller.update([(point_x - 320), 0])
        print("point_x:%d, point_y:%d, radius:%d, z_Pid:%d" % (point_x, point_y, radius, int(z_Pid)))
        self.dog.turn(int(z_Pid))
    
    def cancel(self):
        self.dog.reset()

    def dog_init(self):
        self.dog.stop()
        time.sleep(.01)
        self.dog.pace("slow")
        time.sleep(.01)
        self.dog.translation('z', 90)
        time.sleep(.01)
        self.dog.attitude('p', 10)

    def process(self, rgb_img, action):
        binary = []
        rgb_img = cv.resize(rgb_img, (320,240))
        if button.press_d():
            self.Track_state='init'
            print('state:init')
        if button.press_c():
            self.Track_state='color'
            print('state:color')
        if button.press_a():
            self.Track_state='tracking'
            print('state:tracking')

        if self.Track_state == 'tracking':
            print(self.hsv_range)
            rgb_img, binary, self.circle = self.color.line_follow(rgb_img, self.hsv_range)
            if len(self.circle) != 0:
                self.execute(self.circle[0], self.circle[1], self.circle[2])
        return rgb_img, binary


    def Reset(self):
        self.PID_init()
        self.Track_state = 'init'
        self.hsv_range = ()
        self.dog_init()

    def PID_init(self):
        self.PID_controller = simplePID(
            [0, 0],
            [self.FollowLinePID[0] / 1.0 / (self.scale), 0],
            [self.FollowLinePID[1] / 1.0 / (self.scale), 0],
            [self.FollowLinePID[2] / 1.0 / (self.scale), 0])


if __name__ == '__main__':
    line_detect = LineDetect()
    capture = cv.VideoCapture(0)
    capture.set(3,320)
    capture.set(4,240)
    while capture.isOpened():
        start = time.time()
        ret, frame = capture.read()
        action=32
        frame, binary = line_detect.process(frame, action)
        b,g,r = cv2.split(frame)
        img = cv2.merge((r,g,b))
        imgok = Image.fromarray(img)
        display.ShowImage(imgok)
        if button.press_b():
            line_detect.cancel()
            break
    
    capture.release()
    cv.destroyAllWindows()
