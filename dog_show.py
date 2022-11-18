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
splash = Image.new("RGB", (display.height, display.width ),"white")
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
        splash.paste(exp,(40,0))
        #canvas.draw_image(image.Image().open(pic_path + expression_name_cs + "/" + str(i+1) + ".png"), _canvas_x, _canvas_y)
        display.ShowImage(splash)
        time.sleep(0.05)
        if button.press_b():
            dog.perform(0)  
            sys.exit()
dog.perform(1)        
#Popen(['mplayer','dog.mp3','-loop 0'])
proc=Popen("mplayer dog.mp3 -loop 0", shell=True)
while 1:
    show("sad", 8)
    show("naughty", 8)
    show("boring", 9)
    show("angry", 8)
    show("shame", 7)
    show("surprise", 8)
    show("happy", 6)
    show("sleepy", 8)
    show("drool", 8)
    show("pray", 8)
    show("hate", 10)
    show("love", 9)
    
dog.perform(0)  
proc.kill()
