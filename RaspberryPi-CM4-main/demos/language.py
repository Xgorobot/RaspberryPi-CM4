from robot import *
import numpy as np
from numpy import linalg

sys.path.append("..")

button = Button()
la = load_language()
current_dir = os.getcwd()
language_ini_path = os.path.join(current_dir, "language", "language.ini")

# Colors
color_bg = (8, 10, 26)
color_unselect = (89, 99, 149)
color_select = (24, 47, 223)
color_white = (255, 255, 255)
splash_theme_color = (15, 21, 46)
purple = (24, 47, 223)

# Font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc", 16)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 18)

lan_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/L@2x.png")
arrow_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/C@2x.png")

def display_cjk_string(
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
    splash.text((x, y), text, fill=color, font=font_size)

def lcd_rect(x, y, w, h, color, thickness):
    draw.rectangle([(x, y), (w, h)], fill=color, width=thickness)

current_dir = os.getcwd()

print(current_dir)
language_ini_path = os.path.join(current_dir, "language", "language.ini")

print(language_ini_path)
with open(language_ini_path, "r") as f:
    content = f.read()

print(content)
splash.paste(lan_logo, (133, 25), lan_logo)

text_width = draw.textlength(la["LANGUAGE"]["SET"], font=font2)
title_x = (320 - text_width) / 2
display_cjk_string(
    draw,
    title_x,
    90,
    la["LANGUAGE"]["SET"],
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)
display.ShowImage(splash)

country_list = [
    ["English", "en"],
    ["中文", "cn"],
]
select = 0
while 1:
    draw.rectangle([(20, 145), (300, 180)], fill=purple)
    if content == "cn":
        draw.rectangle([(160, 146), (299, 179)], fill=color_unselect)
    else:
        draw.rectangle([(21, 146), (160, 179)], fill=color_unselect)
    display_cjk_string(
        draw,
        80,
        150,
        "CN",
        font_size=font2,
        color=color_white,
        background_color=color_bg,
    )
    display_cjk_string(
        draw,
        220,
        150,
        "EN",
        font_size=font2,
        color=color_white,
        background_color=color_bg,
    )
    splash.paste(arrow_logo, (148, 150), arrow_logo)
    display.ShowImage(splash)
    if button.press_c():
        content = "cn"
    elif button.press_d():
        content = "en"
    elif button.press_a():
        break
    elif button.press_b():
        os._exit(0)

with open(language_ini_path, "w") as f:
    print('55')
    print(content)
    f.write(content)
    
print("ini writed")
text_width = draw.textlength(la["LANGUAGE"]["SAVED"], font=font2)
title_x = (320 - text_width) / 2
display_cjk_string(
    draw,
    title_x,
    200,
    la["LANGUAGE"]["SAVED"],
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)
display.ShowImage(splash)

time.sleep(2)
os.system('sudo reboot')
