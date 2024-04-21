from subprocess import Popen
import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO

import sys
sys.path.append("..")
import uiutils
la=uiutils.load_language()


#define colors
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)
#display init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
#button
button=Button()
#const
firmware_info='v1.0'
#font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",22)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc",30)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
button=Button()
servo=[11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51, 52, 53]
num = 0
isCollect = 0
n = 0
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",22)

dog = XGO(port='/dev/ttyAMA0',version="xgolite")

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

lcd_draw_string(draw,70,20, la['DOG_VISION_SHOW']['PRESSA'], color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,80, la['DOG_VISION_SHOW']['PRESSB'], color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,140, la['DOG_VISION_SHOW']['PRESSC'], color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,200, la['DOG_VISION_SHOW']['PRESSD'], color=(255,255,255), scale=font2, mono_space=False)
display.ShowImage(splash)

lcd_rect(0,0,320,240,color=color_black,thickness=-1)

start_time=0
time_list=[]
action_num=0
while True:    
    
    if button.press_d(): #TEACH
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        dog.teach('record',action_num)
        dog.teach_arm('record',action_num)
        action_num+=1
        time_list.append(time.time()-start_time)
        lcd_draw_string(draw,110,100, la['DOG_VISION_SHOW']['ACTION']+(str(action_num+1)), color=(255,255,255), scale=font2, mono_space=False)
        lcd_draw_string(draw,20,150,la['DOG_VISION_SHOW']['MAX'], color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)   
        start_time=time.time() 
    if button.press_c():  #READY START
        dog.load_allmotor()
        dog.reset()
        time.sleep(2)
        time_list=[]
        action_num=0
        start_time=time.time()
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        dog.unload_allmotor()
        lcd_draw_string(draw,40,100, la['DOG_VISION_SHOW']['READY'], color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        time.sleep(0.02)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
    if button.press_a():  #ACTION
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        lcd_draw_string(draw,66,100, la['DOG_VISION_SHOW']['EXECUTING'], color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        dog.load_allmotor()
        dog.reset()
        time.sleep(2)
        print(time_list)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)  
        for i in range(action_num):
            dog.teach('play',i)
            dog.teach_arm('play',i)
            time.sleep(time_list[i])
        print('action done!')
        lcd_draw_string(draw,100,100, la['DOG_VISION_SHOW']['DONE'], color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
    if button.press_b():  #QUIT 
        dog.load_allmotor()
        dog.reset()
        break


