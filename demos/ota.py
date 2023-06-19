import xgolib
import time
import random
import os
import sys
import xgoscreen.LCD_2inch as LCD_2inch
import RPi.GPIO as GPIO
from PIL import Image,ImageDraw,ImageFont

import sys
sys.path.append("..")
import uiutils
la=uiutils.load_language()

os.system('sudo chmod 777 /dev/ttyAMA0')
xgo = xgolib.XGO(port = '/dev/ttyAMA0',version='xgomini')
fm=xgo.read_firmware()
filename_mini = "./bin/mini.bin"
filename_lite = "./bin/lite.bin"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
splash = Image.new("RGB",(320,240),"black")
display.ShowImage(splash)

#字体载入
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",50)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",30)
def lcd_text(x,y,content):
        draw = ImageDraw.Draw(splash)
        draw.text((x,y),content,fill = "WHITE",font=font1)
        display.ShowImage(splash)
def lcd_text_1(x,y,content):
        draw = ImageDraw.Draw(splash)
        draw.text((x,y),content,fill = "BLUE",font=font2)
        display.ShowImage(splash)
def lcd_rectangle(x1,y1,x2,y2):
        draw = ImageDraw.Draw(splash)
        draw.rectangle((x1,y1,x2,y2),fill = "WHITE",outline = "WHITE",width = 2)
        display.ShowImage(splash)
def lcd_rectangleN(x1,y1,x2,y2):
        draw = ImageDraw.Draw(splash)
        draw.rectangle((x1,y1,x2,y2),fill = None,outline = "WHITE",width = 2)
        display.ShowImage(splash)
lcd_text(70,60,la['OTA']['BURNING'])
lcd_rectangleN(70,130,250,170)
if fm[0]=='M':
    print('XGO-MINI')
    xgo = xgolib.XGO(port='/dev/ttyAMA0',version="xgomini")
    xgo.upgrade(filename_mini)
else:
    print('XGO-LITE')
    xgo = xgolib.XGO(port='/dev/ttyAMA0',version="xgolite")
    xgo.upgrade(filename_lite)
#xgo.upgrade(filename)
time.sleep(3)
lcd_rectangle(70,130,100,170)
time.sleep(3)
lcd_rectangle(70,130,130,170)
time.sleep(3)
lcd_rectangle(70,130,160,170)
time.sleep(3)
lcd_rectangle(70,130,190,170)
time.sleep(3)
lcd_rectangle(70,130,220,170)
time.sleep(3)
lcd_rectangle(70,130,250,170)
time.sleep(3)
a = xgo.read_firmware()
print(a)
lcd_text_1(90,190,a)
time.sleep(3)
sys.exit()
