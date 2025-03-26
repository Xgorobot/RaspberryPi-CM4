import RPi.GPIO as GPIO
import time,os


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
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


