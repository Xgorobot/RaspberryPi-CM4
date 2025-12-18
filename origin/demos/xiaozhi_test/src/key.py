import RPi.GPIO as GPIO
import time,os
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
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


