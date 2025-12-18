import RPi.GPIO as GPIO
import time,os
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
splash_theme_color = (15, 21, 46)
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
        self.key4=22
        GPIO.setup(self.key1,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key2,GPIO.IN,GPIO.PUD_UP)
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
    def press_d(self):
        last_state=GPIO.input(self.key4)
        if last_state:
            return False
        else:
            while not GPIO.input(self.key4):
                time.sleep(0.02)
            return True


