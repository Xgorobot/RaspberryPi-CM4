from subprocess import Popen
import _thread
import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
import os


display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (320, 240),"white")
display.ShowImage(splash)
draw = ImageDraw.Draw(splash)
button=Button()
#-----------------------COMMON INIT----------------------- 


pic_path = "./expression/"
_canvas_x, _canvas_y = 0, 0

def show(expression_name_cs, pic_num):
    global canvas
    for i in range(0, pic_num):
        filename=pic_path + expression_name_cs + "/" + str(i+1) + ".png"
        exp = Image.open(pic_path + expression_name_cs + "/" + str(i+1) + ".png")
        display.ShowImage(exp)
        time.sleep(0.1)
        if button.press_b():
            dog.perform(0)  
            sys.exit()
dog.perform(1)        
proc=Popen("mplayer dog.mp3 -loop 0", shell=True)
while 1:
    show("sad", 14)
    show("naughty", 14)
    show("boring", 14)
    show("angry", 13)
    show("shame", 11)
    show("surprise", 15)
    show("happy", 12)
    show("sleepy", 19)
    show("seek", 12)
    show("lookaround", 12)
    show("love", 13)
    
dog.perform(0)  
proc.kill()
