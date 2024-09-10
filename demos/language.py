import os, socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
import numpy as np
from numpy import linalg
from xgolib import XGO

import sys, os

sys.path.append("..")
import uiutils

la = uiutils.load_language()
current_dir = os.getcwd()
language_ini_path = os.path.join(current_dir, "language", "language.ini")

button = Button()
# define colors
color_bg = (8, 10, 26)
color_unselect = (89, 99, 149)
color_select = (24, 47, 223)
color_white = (255, 255, 255)
splash_theme_color = (15, 21, 46)
# display init
display = LCD_2inch.LCD_2inch()
display.clear()
# splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
# splash=splash.rotate(180)
display.ShowImage(splash)
# font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc", 12)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 20)


# -----------------------COMMON INIT-----------------------
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
language_ini_path = os.path.join(current_dir, "language", "language.ini")


with open(language_ini_path, "r") as f:
    content = f.read()


display_cjk_string(
    draw,
    15,
    17,
    la["LANGUAGE"]["NOW"] + content,
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)
display_cjk_string(
    draw,
    15,
    77,
    la["LANGUAGE"]["SET"],
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)
display.ShowImage(splash)

country_list = [
    ["English", "en"],
    ["中文", "cn"],
    # ['日本語','jp'],
]
select = 0
while 1:
    lcd_rect(0, 70, 320, 120, (255, 0, 0), -1)
    display_cjk_string(
        draw,
        15,
        77,
        la["LANGUAGE"]["SET"] + country_list[select][0],
        font_size=font2,
        color=color_white,
        background_color=color_bg,
    )
    display.ShowImage(splash)
    if button.press_c():
        if select == 0:
            select = len(country_list) - 1
        else:
            select -= 1
    elif button.press_d():
        if select == len(country_list) - 1:
            select = 0
        else:
            select += 1
    elif button.press_a():
        break
    elif button.press_b():
        time.sleep(0.5)
        sys.exit()


content = country_list[select][1]
print(content)
print("write ini")


with open(language_ini_path, "w") as f:
    f.write(content)


display_cjk_string(
    draw,
    15,
    157,
    la["LANGUAGE"]["SAVED"],
    font_size=font2,
    color=color_white,
    background_color=color_bg,
)
display.ShowImage(splash)
