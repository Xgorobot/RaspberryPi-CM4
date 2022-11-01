from subprocess import Popen
import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO


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
font1 = ImageFont.truetype("msyh.ttc",15)
font2 = ImageFont.truetype("msyh.ttc",22)
font3 = ImageFont.truetype("msyh.ttc",30)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
#splash=splash.rotate(180)
display.ShowImage(splash)
button=Button()
servo=[11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51, 52, 53]
num = 0
isCollect = 0
n = 0
font2 = ImageFont.truetype("msyh.ttc",22)

dog = XGO(port='/dev/ttyAMA0',version="xgolite")

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

lcd_draw_string(draw,70,20, "BUTTON A:RECORD", color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,80, "BUTTON B: STOP", color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,140, "BUTTON C:SHOW", color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,70,200, "BUTTON D:QUIT", color=(255,255,255), scale=font2, mono_space=False)
display.ShowImage(splash)

lcd_rect(0,0,320,240,color=color_black,thickness=-1)
data = [[],[],[],[],[],[],[],[],[],[],[],[]]

dog.unload_allmotor()
time.sleep(2)


while True:    
    
    if button.press_c():
        dog.unload_allmotor()
        data[n] = dog.read_motor()
        print('-----------------')
        print(data)
        lcd_draw_string(draw,70,100, "ACTION"+(str(n+1)), color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        time.sleep(0.02)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        n = n + 1  
    if button.press_d():
        data[n] = dog.read_motor()
        dog.load_allmotor()
        lcd_draw_string(draw,40,100, "ACTIONS READY", color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        time.sleep(0.02)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
    if button.press_b():
        lcd_draw_string(draw,40,100, "ACTIONS SHOW", color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
        time.sleep(0.02)
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)  
        for d in data:
            if d!=[]:
                dog.motor(servo,d)
                time.sleep(0.8)
        print('action done!')
        lcd_draw_string(draw,40,100, "ACTIONS DONE", color=(255,255,255), scale=font2, mono_space=False)
        display.ShowImage(splash)
    if button.press_a():
        break


