import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button

path=os.getcwd()

#define colors
splash_theme_color = (15,21,46)
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splashb_theme_color = (15,21,46)
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
#init splash
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
#splash=splash.rotate(180)
display.ShowImage(splash)
fuck = Image.open('./pics/connect@2x.png')	
print(fuck.size)
splash.paste(fuck)
#image = image.rotate(90)
display.ShowImage(splash)
 