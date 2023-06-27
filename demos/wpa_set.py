import random
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
from numpy import linalg
from xgolib import XGO

import sys
sys.path.append("..")
import uiutils
la=uiutils.load_language()

button=Button()
#define colors
color_bg=(8,10,26)
color_unselect=(89,99,149)
color_select=(24,47,223)
color_white=(255,255,255)
splash_theme_color = (15,21,46)
#display init
display = LCD_2inch.LCD_2inch()
display.clear()
#splash
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)

display.ShowImage(splash)
#font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",12)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",20)

def display_cjk_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = font_size) 
def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

wifi="/etc/wpa_supplicant/wpa_supplicant.conf"



with open(wifi, 'r') as f:
    content=f.read()
    print(content)
    s=content.find('ssid=')
    end=s+6
    while content[end]!='"':
        end+=1
    ssid=content[s+6:end]
    p=content.find('psk=')
    end=p+5
    while content[end]!='"':
        end+=1
    pwd=content[p+5:end]


display_cjk_string(draw,35,77, 'SSID:'+ssid, font_size=font2, color=color_white, background_color=color_bg)
display_cjk_string(draw,35,97, 'PWD:'+pwd, font_size=font2, color=color_white, background_color=color_bg)
display.ShowImage(splash)

print(ssid,pwd)
num = 19

def generate_random_str(randomlength=1):
    global num
    num +=1
    if num == 30:
        num = 20
    else:
        num = num
    '''
    random_str =''
    base_str ='0123456789'
    length =len(base_str) -1
    for i in range(length):
        #random_str +=base_str[random.randint(0, length)]
        num += 1
    '''
    return str(num)

def makefile(s,p):
    t1='''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CN

network={
    ssid="'''
    t2='''
    key_mgmt=WPA-PSK
    }
    '''
    t3='''"
    psk="'''
    files=t1+s+t3+p+'"'+t2
    print(files)
    return files

select=0 
while 1:
    lcd_rect(0,73,320,125,(255,0,0),-1)
    display_cjk_string(draw,35,77, 'SSID:'+ssid, font_size=font2, color=color_white, background_color=color_bg)
    display_cjk_string(draw,35,97, 'PWD:'+pwd, font_size=font2, color=color_white, background_color=color_bg)
    display.ShowImage(splash)
    if button.press_c():
        ssid='XGO2'
        pwd='LuwuDynamics'
        fc=makefile(ssid,pwd)
        with open(wifi, 'w') as f:
            f.write(fc)
    elif button.press_d():
        ssid='XGO'+generate_random_str(1)
        pwd='12345678'
        fc=makefile(ssid,pwd)
        with open(wifi, 'w') as f:
            f.write(fc)
    elif button.press_a():
        display_cjk_string(draw,35,77, 'SSID:'+ssid, font_size=font2, color=color_white, background_color=color_bg)
        display_cjk_string(draw,35,97, 'PWD:'+pwd, font_size=font2, color=color_white, background_color=color_bg)
        display_cjk_string(draw,15,157, la['WIFISET']['SAVED'], font_size=font2, color=color_white, background_color=color_bg)
        display.ShowImage(splash)
        time.sleep(1)
        break
    elif button.press_b():
        sys.exit()





