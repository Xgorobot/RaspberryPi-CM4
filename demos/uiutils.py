import RPi.GPIO as GPIO
import time,os,json

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
    current_dir = os.getcwd()
    language_ini_path = os.path.join(current_dir, "language", "language.ini")
    with open(language_ini_path,'r') as f:#r为标识符，表示只读
        language=f.read()
    language_pack=os.path.join(current_dir, "language", language+".la")
    with open(language_pack,'r') as f:#r为标识符，表示只读
        language_json=f.read()
    language_dict=json.loads(language_json)
    return language_dict
    
