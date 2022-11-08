import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO


 

path=os.getcwd()
# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0 
device = 0
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
firmware_info='v1.1'
#font
font1 = ImageFont.truetype("msyh.ttc",15)
font2 = ImageFont.truetype("msyh.ttc",22)
font3 = ImageFont.truetype("msyh.ttc",30)
#init splash
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
#splash=splash.rotate(180)
display.ShowImage(splash)
#dog
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

def show_battery():
    lcd_rect(270,0,320,5,color=splash_theme_color,thickness=-1)
    draw.bitmap((270,4),bat)
    try:
        battery=dog.read_battery()
        print(battery)
        if len(str(battery))==3:
            lcd_draw_string(draw, 274, 4,str(battery), color=color_white, scale=font1)
        elif len(str(battery))==2:
            lcd_draw_string(draw, 280, 4,str(battery), color=color_white, scale=font1)
        elif len(str(battery))==1:
            lcd_draw_string(draw, 286, 4,str(battery), color=color_white, scale=font1)
        else:
            pass
    except:
        print('uart error!')

#draw methods
def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

def main_program():
    global key_state_left, key_state_right, key_state_down, current_selection

    key_state_left=0
    key_state_down=0
    key_state_right=0
    
    if button.press_a():
        key_state_down=1
        key_state_left=0
        key_state_right=0
    elif button.press_c():
        key_state_down=0
        key_state_left=1
        key_state_right=0
    elif button.press_d():
        key_state_down=0
        key_state_left=0
        key_state_right=1
    elif button.press_b():
        print('b button,but nothing to quit')
    #print(key_state_down,key_state_left,key_state_right)

    if key_state_left == 1 :
        show_battery()
        current_selection = 1
        lcd_rect(0,188,160,240,color=btn_selected,thickness=-1)
        lcd_draw_string(draw, 25, 195, "Program", color=color_white, scale=font2)
        lcd_rect(160,188,320,240,color=btn_unselected,thickness=-1)
        lcd_draw_string(draw, 181, 195, "Try demos", color=color_white, scale=font2)

    if key_state_right == 1 :
        show_battery()
        current_selection = 2
        lcd_rect(0,188,160,240,color=btn_unselected,thickness=-1)
        lcd_draw_string(draw, 25, 195, "Program", color=color_white, scale=font2)
        lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
        lcd_draw_string(draw, 181, 195, "Try demos", color=color_white, scale=font2)

    if key_state_down == 1:
        show_battery()
        if current_selection == 1: 
            print("edublock")
            lcd_rect(0,188,160,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 25, 195, "Opening...", color=color_white, scale=font2)
            time.sleep(1)
            #import edublock
            os.system("sudo python edublock.py")
            lcd_rect(0,188,160,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 25, 195, "Program", color=color_white, scale=font2)

        if current_selection == 2: 
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, "Opening...", color=color_white, scale=font2)
            time.sleep(1)
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, "Try demos", color=color_white, scale=font2)
            #__import__("try_demo-cs.py")
            print('turn demos')
            os.system("sudo python demoen.py")



        print(str(current_selection) + " select")
    display.ShowImage(splash)

#-------------------------init UI---------------------------------
logo = Image.open("./pics/luwu@3x.png")
draw.bitmap((74,49),logo)
lcd_draw_string(draw,217, 133, firmware_info, color=color_white, scale=font1)
wifiy = Image.open("./pics/wifi@2x.png")
wifin = Image.open("./pics/wifi-un@2x.png")
bat = Image.open("./pics/battery.png")


lcd_rect(0,188,320,240,color=btn_unselected,thickness=1)
lcd_rect(0,188,160,240,color=btn_selected,thickness=1)
lcd_draw_string(draw, 30,195, "Program", color=color_white, scale=font2)
lcd_draw_string(draw, 181, 195, "Try demos", color=color_white,scale=font2) 
show_battery()
display.ShowImage(splash)


current_selection = 1

while True:
    main_program()

display.module_exit()
