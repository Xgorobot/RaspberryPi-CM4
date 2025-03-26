import RPi.GPIO as GPIO
import time,os,json,sys,random,re
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#Color Define
splash_theme_color = (15, 21, 46)
btn_selected = (24, 47, 223)
btn_unselected = (20, 30, 53)
txt_selected = (255, 255, 255)
txt_unselected = (76, 86, 127)
splash_theme_color = (15, 21, 46)
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_red = (238, 55, 59)
mic_purple = (24, 47, 223)

#PIC Loading
mic_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic.png")
mic_wave = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic_wave.png")
offline_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/offline.png")
draw_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/gpt_draw.png")

# Font Cache
_font_cache = {}

def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype("/home/pi/model/msyh.ttc", size)
    return _font_cache[size]
# Define Font
font1 = get_font(15)
font2 = get_font(16)
font3 = get_font(18)

# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)


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

#################### Draw Designs ####################
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
    Clear Top
'''
def clear_top():
    draw.rectangle([(0, 0), (320, 111)], fill=splash_theme_color)

'''
    Clear Bottom
'''
def clear_bottom():
    draw.rectangle([(0, 111), (320, 240)], fill=splash_theme_color)

'''
    Draw Wave
'''
def draw_wave(ch):
    if ch > 10:
        ch = 10
    start_x = 40
    start_y = 32
    width, height = 80, 50
    y_center = height // 2
    current_y = y_center
    previous_point = (0 + start_x, y_center + start_y)
    clear_top()
    draw.bitmap((145, 40), mic_logo, mic_purple)
    x = 0
    while x < width:
        segment_length = random.randint(7, 25)
        gap_length = random.randint(4, 20)

        for _ in range(segment_length):
            if x >= width:
                break
            amplitude_change = random.randint(-ch, ch)
            current_y += amplitude_change
            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1
            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill=mic_purple)
            previous_point = current_point
            x += 1
        for _ in range(gap_length):
            if x >= width:
                break
            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill=mic_purple, width=2)
            previous_point = current_point
            x += 1
    start_x = 210
    start_y = 32
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
            amplitude_change = random.randint(-ch, ch)
            current_y += amplitude_change
            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1
            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill=mic_purple)
            previous_point = current_point
            x += 1
        for _ in range(gap_length):
            if x >= width:
                break
            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill=mic_purple, width=2)
            previous_point = current_point
            x += 1

'''
    Draw Cir
'''
def draw_cir(ch):
    if ch > 15:
        ch = 15
    clear_top()
    draw.bitmap((145, 40), mic_logo, mic_purple)
    radius = 4
    cy = 60
    centers = [(62, cy), (87, cy), (112, cy), (210, cy), (235, cy), (260, cy)]
    for center in centers:
        random_offset = random.randint(0, ch)
        new_y = center[1] + random_offset
        new_y2 = center[1] - random_offset

        draw.line([center[0], new_y2, center[0], new_y], fill=mic_purple, width=11)

        top_left = (center[0] - radius, new_y - radius)
        bottom_right = (center[0] + radius, new_y + radius)
        draw.ellipse([top_left, bottom_right], fill=mic_purple)
        top_left = (center[0] - radius, new_y2 - radius)
        bottom_right = (center[0] + radius, new_y2 + radius)
        draw.ellipse([top_left, bottom_right], fill=mic_purple)

'''
   Draw Wait 
'''
def draw_wait(j):
    center = (161, 56)
    initial_radius = 50 - j * 8
    clear_top()
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)
        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )
    draw.bitmap(
        (145, 40),
        mic_wave,
    )
    display.ShowImage(splash)

'''
    Draw Play
'''
def draw_play():
    j = 0
    center = (161, 56)
    initial_radius = 50 - j * 8
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)
        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )
    image_height = 50
    line_width = 3
    spacing = 3
    start_x = 146 + spacing
    for _ in range(5):
        line_length = random.randint(3, 20)
        start_y = (image_height - line_length) // 2 + 30
        end_y = start_y + line_length
        draw.line((start_x, start_y, start_x, end_y), fill="white", width=line_width)
        draw.point((start_x, start_y - 1), fill="white")
        draw.point((start_x, end_y + 1), fill="white")
        start_x += line_width + spacing
    display.ShowImage(splash)

'''
    Draw Offline
'''
def draw_offline():
    draw.bitmap((115, 20), offline_logo, "red")
    warn_text = "Wifi未连接或无网络"
    draw.text((88, 150), warn_text, fill=(255, 255, 255), font=font3)
    display.ShowImage(splash)

'''
    Draw Draw
'''
def draw_draw(j):
    center = (161, 86)
    initial_radius = 50 - j * 8
    draw.rectangle([(0, 0), (320, 240)], fill=splash_theme_color)
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)
        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )
    draw.bitmap(
        (147, 72),
        draw_logo,
    )
    display.ShowImage(splash)
