import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
import uiutils
from xgolib import XGO

la=uiutils.load_language()

os.system("sudo chmod 777 -R /dev/ttyAMA0")
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
fm=dog.read_firmware()
if fm[0]=='M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0',version="xgomini")
    dog_type='M'
else:
    print('XGO-LITE')
    dog_type='L'
dog.reset()

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
button=uiutils.Button()
#const
if dog_type=='M':
    firmware_info='MINI'
elif dog_type=='L':
    firmware_info='LITE'
#font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",22)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc",30)
#init splash
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
#splash=splash.rotate(180)
display.ShowImage(splash)
#dog
os.system('sudo chmod 777 /dev/ttyAMA0')
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

current_selection=1

def show_battery():
    lcd_rect(200,0,320,25,color=splash_theme_color,thickness=-1)
    draw.bitmap((270,4),bat)
    try:
        battery=dog.read_battery()
        print(battery)
        if str(battery)=='0':
            print('uart error')
            lcd_rect(200,0,320,15,color=splash_theme_color,thickness=-1)
            draw.bitmap((270,4),bat)
        else:
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
        if current_selection==1:
            current_selection=1
        else:
            current_selection-=1

    if key_state_right == 1 :
        show_battery()
        if current_selection==3:
            current_selection=3
        else:
            current_selection+=1

    if current_selection==1:
        lcd_rect(0,188,320,240,color=btn_unselected,thickness=-1)
        lcd_rect(0,188,110,240,color=btn_selected,thickness=-1)
        lcd_draw_string(draw, 7, 195, la['MAIN']['PROGRAM'], color=color_white, scale=font2)
        lcd_draw_string(draw, 120, 195, la['MAIN']['RC'], color=color_white, scale=font2)
        lcd_draw_string(draw, 215, 195, la['MAIN']['TRYDEMO'], color=color_white, scale=font2)
        draw.line((110,188,110,240),fill=txt_unselected,width=1,joint=None)
        draw.line((210,188,210,240),fill=txt_unselected,width=1,joint=None)
        draw.rectangle((0,188,320,240),outline=txt_unselected,width=1)
    elif current_selection==2:
        lcd_rect(0,188,320,240,color=btn_unselected,thickness=-1)
        lcd_rect(110,188,210,240,color=btn_selected,thickness=-1)
        lcd_draw_string(draw, 7, 195, la['MAIN']['PROGRAM'], color=color_white, scale=font2)
        lcd_draw_string(draw, 120, 195, la['MAIN']['RC'], color=color_white, scale=font2)
        lcd_draw_string(draw, 215, 195, la['MAIN']['TRYDEMO'], color=color_white, scale=font2)
        draw.line((110,188,110,240),fill=txt_unselected,width=1,joint=None)
        draw.line((210,188,210,240),fill=txt_unselected,width=1,joint=None)
        draw.rectangle((0,188,320,240),outline=txt_unselected,width=1)
    elif current_selection==3:
        lcd_rect(0,188,320,240,color=btn_unselected,thickness=-1)
        lcd_rect(210,188,320,240,color=btn_selected,thickness=-1)
        lcd_draw_string(draw, 7, 195, la['MAIN']['PROGRAM'], color=color_white, scale=font2)
        lcd_draw_string(draw, 120, 195, la['MAIN']['RC'], color=color_white, scale=font2)
        lcd_draw_string(draw, 215, 195,la['MAIN']['TRYDEMO'], color=color_white, scale=font2)
        draw.line((110,188,110,240),fill=txt_unselected,width=1,joint=None)
        draw.line((210,188,210,240),fill=txt_unselected,width=1,joint=None)
        draw.rectangle((0,188,320,240),outline=txt_unselected,width=1)

    if key_state_down == 1:
        show_battery()
        if current_selection == 1: 
            print("edublock")
            lcd_rect(0,188,160,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 25, 195,la['MAIN']['OPENING'], color=color_white, scale=font2)
            time.sleep(1)
            os.system("python3 edublock.py")
            lcd_rect(0,188,160,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 25, 195, la['MAIN']['PROGRAM'], color=color_white, scale=font2)

        if current_selection == 2: 
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, la['MAIN']['OPENING'], color=color_white, scale=font2)
            time.sleep(1)
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, la['MAIN']['TRYDEMO'], color=color_white, scale=font2)
            print('turn demos')
            os.system("python3 app/app_dogzilla.py")
            
        if current_selection == 3: 
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, la['MAIN']['OPENING'], color=color_white, scale=font2)
            time.sleep(1)
            lcd_rect(160,188,320,240,color=btn_selected,thickness=-1)
            lcd_draw_string(draw, 181, 195, la['MAIN']['TRYDEMO'], color=color_white, scale=font2)
            #__import__("try_demo-cs.py")
            print('turn demos')
            os.system("python3 demoen.py")


        print(str(current_selection) + " select")
    display.ShowImage(splash)

#-------------------------init UI---------------------------------
logo = Image.open("./pics/luwu@3x.png")
draw.bitmap((74,49),logo)
lcd_draw_string(draw,210,133, firmware_info, color=color_white, scale=font1)
wifiy = Image.open("./pics/wifi@2x.png")
wifin = Image.open("./pics/wifi-un@2x.png")
bat = Image.open("./pics/battery.png")

show_battery()
current_selection = 1

while True:
    main_program()

display.module_exit()
