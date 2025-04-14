from xgolib import XGO
from PIL import Image, ImageDraw, ImageFont
import spidev as SPI
import time,os,json,random,sys,socket,re
import RPi.GPIO as GPIO
import xgoscreen.LCD_2inch as LCD_2inch

# Raspberry Pi GPIO model
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Define Colors
btn_selected = (24, 47, 223)
btn_unselected = (20, 30, 53)
txt_selected = (255, 255, 255)
txt_unselected = (76, 86, 127)
splash_theme_color = (15, 21, 46)
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_red = (238, 55, 59)


# Font Cache
_font_cache = {}

def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype("/home/pi/model/msyh.ttc", size)
    return _font_cache[size]
# Define Font
font1 = get_font(15)
font2 = get_font(22)
font3 = get_font(30)
font4 = get_font(40)

bat = Image.open(os.path.join("/home/pi/RaspberryPi-CM4-main/", "pics", "battery.png"))
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
    #Lower Right Button
    def press_a(self):
        last_state=GPIO.input(self.key1)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key1):
                time.sleep(0.02)
            return True
    #Lower Left Button
    def press_b(self):
        last_state=GPIO.input(self.key2)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key2):
                time.sleep(0.02)
            os.system('pkill mplayer')
            return True
    #Upper left Button
    def press_c(self):
        last_state=GPIO.input(self.key3)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key3):
                time.sleep(0.02)
            return True
    #Upper Right Button
    def press_d(self):
        last_state=GPIO.input(self.key4)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key4):
                time.sleep(0.02)
            return True
'''
    Loading Language Information 
'''

def load_language():
    current_dir = os.getcwd()
    print(current_dir)
    language_ini_path = os.path.join(current_dir, "language", "language.ini")
    print(language_ini_path)
    with open(language_ini_path, 'r') as f:
        language = f.read().strip()
        print(language)
    language_pack = os.path.join(current_dir, "language", language + ".la")
    print(language_pack)
    with open(language_pack, 'r') as f:
        language_json = f.read()
    cleaned_json = re.sub(r'[\x00-\x1f\x7f]', '', language_json)
    language_dict = json.loads(cleaned_json)
    return language_dict

'''
    Loading Language Information From language.ini
'''
def language():
    current_dir = os.getcwd()
    print(current_dir)
    language_ini_path = os.path.join(current_dir, "language", "language.ini")
    print(language_ini_path)
    with open(language_ini_path,'r') as f:
        language=f.read()
        result_la = language.strip()
        print(result_la)
    return result_la
'''
    Init Serial Port And Load The Product Version
'''
# 缓存 XGO 对象和权限设置
global _dog_type_cache
global _dog_instance_cache 
global _is_permissions_set 
global dog
def check_type():
    global _dog_type_cache
    global _dog_instance_cache 
    global _is_permissions_set
    global dog
    _dog_type_cache = None
    dog = None
    _is_permissions_set = False
    # 如果缓存中已有信息，直接返回
    if _dog_type_cache is not None:
        return _dog_type_cache

    # 如果尚未设置权限，且需要设置权限，只执行一次
    if not _is_permissions_set:
        os.system("sudo chmod 777 -R /dev/ttyAMA0")
        _is_permissions_set = True

    # 如果缓存中没有 XGO 对象，创建并缓存它
    if dog is None:
        dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    # 读取固件信息
    fm = dog.read_firmware()
    #if it's Mini or Lite
    if fm[0] == "M":
        dog_type = "M"
        firmware_info = "MINI"
        version = "xgomini"
    else:
        dog_type = "L"
        firmware_info = "LITE"
        version = "xgolite"

    # 缓存结果（dog_type, firmware_info, version）
    _dog_type_cache = (dog_type, version, firmware_info)

    return dog_type, firmware_info,version 

# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

dog_type,firmware_info,version = check_type()
print(version)

'''
    Battery Level Display
'''
def show_battery():
    lcd_rect(200, 0, 320, 25, color=splash_theme_color, thickness=-1)
    draw.bitmap((270, 4), bat)
    try:
        battery = dog.read_battery()
        print(f"Battery power is {battery}")
        if str(battery) == "0":
            print("uart error")
            lcd_rect(200, 0, 320, 15, color=splash_theme_color, thickness=-1)
            draw.bitmap((270, 4), bat)
        else:
            if len(str(battery)) == 3:
                lcd_draw_string(
                    draw, 274, 4, str(battery), color=color_white, scale=font1
                )
            elif len(str(battery)) == 2:
                lcd_draw_string(
                    draw, 280, 4, str(battery), color=color_white, scale=font1
                )
            elif len(str(battery)) == 1:
                lcd_draw_string(
                    draw, 286, 4, str(battery), color=color_white, scale=font1
                )
            else:
                pass
    except:
        print("uart error!")

'''
    Draw Cir
'''
def draw_cir(ch):
    draw.rectangle([(55, 40), (120, 100)], fill=splash_theme_color)
    draw.rectangle([(205, 40), (270, 100)], fill=splash_theme_color)
    radius = 4
    cy = 70

    centers = [(62, cy), (87, cy), (112, cy), (210, cy), (235, cy), (260, cy)]

    for center in centers:
        random_offset = ch
        new_y = center[1] + random_offset
        new_y2 = center[1] - random_offset
        draw.line([center[0], new_y2, center[0], new_y], fill="white", width=11)

        top_left = (center[0] - radius, new_y - radius)
        bottom_right = (center[0] + radius, new_y + radius)
        draw.ellipse([top_left, bottom_right], fill="white")
        top_left = (center[0] - radius, new_y2 - radius)
        bottom_right = (center[0] + radius, new_y2 + radius)
        draw.ellipse([top_left, bottom_right], fill="white")
'''
    Draw Wave
'''
def draw_wave(ch):
    start_x = 40
    start_y = 42
    width, height = 80, 50
    y_center = height // 2
    current_y = y_center
    previous_point = (0 + start_x, y_center + start_y)
    draw.rectangle(
        [(start_x - 1, start_y), (start_x + width, start_y + height)],
        fill=splash_theme_color,
    )

    x = 0
    while x < width:
        segment_length = random.randint(7, 25)
        gap_length = random.randint(4, 20)

        for _ in range(segment_length):
            if x >= width:
                break

            amplitude_change = ch
            current_y += amplitude_change

            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1

            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill="white")
            previous_point = current_point
            x += 1

        for _ in range(gap_length):
            if x >= width:
                break

            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill="white", width=2)
            previous_point = current_point
            x += 1

    start_x = 210
    start_y = 42
    width, height = 80, 50
    y_center = height // 2
    current_y = y_center
    previous_point = (0 + start_x, y_center + start_y)
    draw.rectangle(
        [(start_x - 1, start_y), (start_x + width, start_y + height)],
        fill=splash_theme_color,
    )

    x = 0
    while x < width:
        segment_length = random.randint(7, 25)
        gap_length = random.randint(4, 20)

        for _ in range(segment_length):
            if x >= width:
                break

            amplitude_change = ch
            current_y += amplitude_change

            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1

            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill="white")
            previous_point = current_point
            x += 1

        for _ in range(gap_length):
            if x >= width:
                break

            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill="white", width=2)
            previous_point = current_point
            x += 1
'''
    LCD Draw String
'''
def lcd_draw_string(
    splash,
    x,
    y,
    text,
    color=(255, 255, 255),
    font_size=1,
    scale=1,
    mono_space=False,
    auto_wrap=True,
    background_color=(0, 0, 0),
):
    splash.text((x, y), text, fill=color, font=scale)
'''
    LCD Rect
'''
def lcd_rect(x, y, w, h, color, thickness):
    draw.rectangle([(x, y), (w, h)], fill=color, width=thickness)
'''
    Get _dog_type_cache
'''
def get_dog_type_cache():
    global _dog_type_cache
    return _dog_type_cache
