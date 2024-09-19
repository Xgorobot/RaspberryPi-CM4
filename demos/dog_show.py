from subprocess import Popen
import os, socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
from xgolib import XGO
import os

from uiutils import *

# -----------------------COMMON INIT-----------------------
os.system("sudo chmod 777 -R /dev/ttyAMA0")
dog = XGO(port="/dev/ttyAMA0", version="xgolite")
fm = dog.read_firmware()
if fm[0] == "M":
    print("XGO-MINI")
    dog = XGO(port="/dev/ttyAMA0", version="xgomini")
    dog_type = "M"
elif fm[0] == "L":
    print("XGO-LITE")
    dog_type = "L"
elif fm[0] == "R":
    print("XGO-RIDER")
    dog = XGO(port="/dev/ttyAMA0", version="xgorider")
    dog_type = "R"
dog.reset()

pic_path = "./demos/expression/"


def show(expression_name_cs, pic_num):
    global canvas
    for i in range(0, pic_num):
        exp = Image.open(pic_path + expression_name_cs + "/" + str(i + 1) + ".png")
        display.ShowImage(exp)
        time.sleep(0.1)
        if button.press_b():
            dog.perform(0)
            sys.exit()


def show_rider(expression_name_cs, pic_num):
    global canvas
    for i in range(0, pic_num):
        exp = Image.open(
            pic_path
            + "rider/"
            + expression_name_cs
            + "/"
            + expression_name_cs
            + str(i + 1)
            + ".png"
        )
        display.ShowImage(exp)
        time.sleep(0.01)
        if button.press_b():
            dog.perform(0)
            sys.exit()


dog.perform(1)
proc = Popen("mplayer ./demos/Dream.mp3 -loop 0", shell=True)

dog_type = "R"

if dog_type == "L" or dog_type == "M":
    while 1:
        show("sad", 14)
        show("naughty", 14)
        show("boring", 14)
        show("angry", 13)
        show("shame", 11)
        show("surprise", 15)
        show("happy", 12)
        show("sleepy", 19)
        show("seek", 12)
        show("lookaround", 12)
        show("love", 13)
        show("awkwardness", 11)
        show("eyes", 15)
        show("guffaw", 8)
        show("query", 7)
        show("Shakehead", 7)
        show("Stun", 8)
        show("wronged", 14)
elif dog_type == "R":
    while 1:
        show_rider("like", 83)
        show_rider("sad", 65)
        show_rider("Angry", 55)
        show_rider("cute", 76)
        show_rider("doubt", 64)
        show_rider("embarrassed", 66)
        show_rider("grievance", 72)
        show_rider("hate", 81)
        show_rider("laugh", 51)
        show_rider("shy", 60)
        show_rider("sleep", 94)
        show_rider("surprised", 74)
        show_rider("vertigo", 59)


dog.perform(0)
proc.kill()
