import snowboydecoder
import sys
import signal
from xgolib import XGO
import time
import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import threading

# sudo python3 speech.py 1.pmdl 2.pmdl 3.pmdl 4.pmdl 11.pmdl 12.pmdl 18.pmdl 19.pmdl

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
#font
font1 = ImageFont.truetype("msyh.ttc",15)
font2 = ImageFont.truetype("msyh.ttc",22)
font3 = ImageFont.truetype("msyh.ttc",30)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
button=Button()

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)
    
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
lcd_draw_string(draw,30,60, "WAITING FOR COMMAND", color=(255,255,255), scale=font2, mono_space=False)
display.ShowImage(splash)

# Demo code for listening to two hotwords at the same time

interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

def callback1():
    dog.action(1)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "LIE DOWN", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback2():
    dog.action(2)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "STAND UP", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback3():
    dog.action(3)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "CRAWING", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback4():
    dog.action(4)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "TURAN AROUND", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback5():
    dog.action(11)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "PISS", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback6():
    dog.action(12)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "SITDOWN", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)
def callback7():
    dog.action(18)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "BEG FOR FOOD", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)    
def callback8():
    dog.action(19)
    lcd_rect(30,160,320,240,color=splash_theme_color,thickness=-1)
    lcd_draw_string(draw,30,160, "HANDSHAKE", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    time.sleep(5)


models = sys.argv[1:]

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

sensitivity = [0.45]*len(models)
detector = snowboydecoder.HotwordDetector(models, sensitivity=sensitivity)
callbacks = [callback1,
             callback2,
             callback3,
             callback4,
             callback5,
             callback6,
             callback7,
             callback8]


print('Listening... Press Ctrl+C to exit')

# main loop
# make sure you have the same numbers of callbacks and models
detector.start(detected_callback=callbacks,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)

detector.terminate()

print('end?')

