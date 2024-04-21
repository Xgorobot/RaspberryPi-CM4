import RPi.GPIO as GPIO
import time,os,json
from xgolib import XGO
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


class Button:
    def __init__(self):
        self.key1=24
        self.key2=23
        self.key3=17
        self.key4=22
        GPIO.setup(self.key1,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key2,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key3,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key4,GPIO.IN,GPIO.PUD_UP)
    
    def press_a(self):
        last_state=GPIO.input(self.key1)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key1):
                time.sleep(0.02)
            return True

    def press_b(self):
        last_state=GPIO.input(self.key2)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key2):
                time.sleep(0.02)
            os.system('pkill mplayer')
            return True
    
    def press_c(self):
        last_state=GPIO.input(self.key3)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key3):
                time.sleep(0.02)
            return True
    def press_d(self):
        last_state=GPIO.input(self.key4)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key4):
                time.sleep(0.02)
            return True

def load_language():
    #返回当前的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    #test
    print(current_dir)
    #用于路径拼接文件路径
    language_ini_path = os.path.join(current_dir, "language", "language.ini")
    #test
    print(language_ini_path)
    with open(language_ini_path,'r') as f:#r为标识符，表示只读
        language=f.read()
        #test
        print(language)
    language_pack=os.path.join(current_dir, "language", language+".la")
    #test
    print(language_pack)
    with open(language_pack,'r') as f:#r为标识符，表示只读
        language_json=f.read()
    #读取到这个文件中的所有内容，并且读取的结果返回为python的dict对象
    language_dict=json.loads(language_json)
    return language_dict

def language():
    #返回当前的目录
    current_dir = os.getcwd()
    #test
    print(current_dir)
    #用于路径拼接文件路径
    language_ini_path = os.path.join(current_dir, "language", "language.ini")
    #test
    print(language_ini_path)
    with open(language_ini_path,'r') as f:#r为标识符，表示只读
        language=f.read()
        #test
        print(language)
    return language

def check_type():
    os.system("sudo chmod 777 -R /dev/ttyAMA0")
    dog = XGO(port='/dev/ttyAMA0',version="xgorider")
    fm=dog.read_firmware()
    print(fm)
    if fm[0]=='M':
        print('XGO-MINI')
        dog = XGO(port='/dev/ttyAMA0',version="xgomini")
        dog_type='M'
    elif fm[0]=='L':
        print('XGO-LITE')
        dog_type='L'
    elif fm[0]=='R':
        print('XGO-RIDER')
        dog_type='R'
    dog.reset()
    return dog_type


la=load_language()
dog_type=check_type()
print(dog_type)

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
#type
if dog_type=='M':
    firmware_info='MINI'
    version="xgomini"
elif dog_type=='L':
    firmware_info='LITE'
    version="xgolite"
elif dog_type=='R':
    firmware_info='RIDER'
    version="xgorider"
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
dog = XGO(port='/dev/ttyAMA0',version=version)

    
