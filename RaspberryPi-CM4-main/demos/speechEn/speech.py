import os, re
import socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from xgolib import XGO
from PIL import Image, ImageDraw, ImageFont
import threading
import json, base64
import subprocess
import pyaudio
import wave
import numpy as np
from scipy import fftpack
from datetime import datetime
from key import Button

from audio import start_recording
from language_recognize import test_one
from doubao import model_output

splash_theme_color = (15, 21, 46)
font2=ImageFont.truetype("/home/pi/model/msyh.ttc", 20)

# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

def lcd_draw_string(splash, x, y, text, color=(255, 255, 255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0, 0, 0)):
    splash.text((x, y), text, fill=color, font=scale)

def show_words_dog():
    lcd_draw_string(draw, 50, 100, "Command Not Found", color=(0, 255, 255), scale=font2, mono_space=False)
    
    display.ShowImage(splash)

dog = XGO(port='/dev/ttyAMA0', version="xgomini")
button = Button()

def check_button_b():
    """独立线程监测B键，按下时退出程序"""
    while True:
        if button.press_b():
            print("B 键按下, 退出程序")
            os._exit(0)
        time.sleep(0.1)

# 启动按键检测线程
button_thread = threading.Thread(target=check_button_b, daemon=True)
button_thread.start()

import requests
net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    while True:
        try:
            start_recording() 
            content = test_one() 
            
            if content == 0:
                print("录音出错")
                continue 
            
            print(content)

            Dance,Pushups,Pee,Stretch,Pray,Chickenhead,Lookforfood,Grabdownwards,Wave,Beg =model_output(content=content)

            if int(Dance) == 1:
                print("Dance")
                dog.action(23)
                time.sleep(6)
            elif int(Pushups) == 1:
                print("Pushups")
                dog.action(21)
                time.sleep(8)
            elif int(Pee) == 1:
                print("Pee")
                dog.action(11)
                time.sleep(7)
            elif int(Stretch) == 1:
                print("Stretch")
                dog.action(14)
                time.sleep(10)
            elif int(Pray) == 1:
                print("Pray")
                dog.action(19)
                time.sleep(3)
            elif int(Chickenhead) == 1:
                print("Chickenhead")
                dog.action(20)
                time.sleep(9)
            elif int(Lookforfood) == 1:
                print("Lookforfood")
                dog.action(17)
                time.sleep(4)
            elif int(Grabdownwards) == 1:
                print("Grabdownwards")
                dog.action(130)
                time.sleep(10)
            elif int(Wave) == 1:
                print("Wave")
                dog.action(15)
                time.sleep(6)
            elif int(Beg) == 1:
                print("Beg")
                dog.action(17)
                time.sleep(3)
            else:
                show_words_dog()
                print("The command None")
                dog.reset()
            
            time.sleep(1)

        except KeyboardInterrupt:
            print("程序终止")
            break 
        except Exception as e:
            print(f"发生错误: {e}")
            continue
else:
    print("Net is unconnection")
