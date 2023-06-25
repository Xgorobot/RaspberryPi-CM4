import os,socket,sys,time
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button

import sys
sys.path.append("..")
import uiutils
la=uiutils.load_language()
print('zz')
print(la)

button=Button()

color_bg=(8,10,26)
color_unselect=(89,99,149)
color_select=(24,47,223)
color_white=(255,255,255)
splash_theme_color = (15,21,46)

display = LCD_2inch.LCD_2inch()
display.clear()
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


display_cjk_string(draw,15,17, la['VOLUME']['VOLUMe'], font_size=font2, color=color_white, background_color=color_bg)
display.ShowImage(splash)

country_list=[
    ['20%'],
    ['40%'],
    ['60%'],
    ['80%'],
    ['100%'],
]
select=0

while 1:
    lcd_rect(0,70,320,120,(255,0,0),-1)
    display_cjk_string(draw,15,77, la['VOLUME']['PERCENT']+country_list[select][0], font_size=font2, color=color_white, background_color=color_bg)
    display.ShowImage(splash)
    if button.press_c():
        if select==0:
            select=len(country_list)-1
        else:
            select-=1
    elif button.press_d():
        if select==len(country_list)-1:
            select=0
        else:
            select+=1
    elif button.press_a():
        break
    elif button.press_b():
        #display_cjk_string(draw,15,157, la['VOLUME']['QUIT'], font_size=font2, color=color_white, background_color=color_bg)
        #display.ShowImage(splash)
        time.sleep(0.5)
        sys.exit()


ct_code=country_list[select][0]
print(ct_code)
if ct_code == '20%':
	os.system('pactl set-sink-volume 1 20%')
elif ct_code == '40%':
	os.system('pactl set-sink-volume 1 40%')
elif ct_code == '60%':
	os.system('pactl set-sink-volume 1 60%')
elif ct_code == '80%':
	os.system('pactl set-sink-volume 1 80%')
elif ct_code == '100%':
	os.system('pactl set-sink-volume 1 100%')	
display_cjk_string(draw,15,157, la['VOLUME']['SAVED'], font_size=font2, color=color_white, background_color=color_bg)
display.ShowImage(splash)





