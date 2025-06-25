import RPi.GPIO as GPIO
import time
import os

# Raspberry Pi GPIO model
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class Button:
    def __init__(self):
        self.key1=24 # Lower Right
        self.key2=23 # Lower Left
        self.key3=17 # Upper Left
        self.key4=22 # Upper Right
        GPIO.setup(self.key1,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key2,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key3,GPIO.IN,GPIO.PUD_UP)
        GPIO.setup(self.key4,GPIO.IN,GPIO.PUD_UP)

    #Lower Right Button - Original press_a
    def press_lower_right(self):
        last_state=GPIO.input(self.key1)
        if last_state:
            return False
        else:
            # Wait for release
            while not GPIO.input(self.key1):
                time.sleep(0.02)
            return True

    #Lower Left Button - Original press_b
    def press_lower_left(self):
        last_state=GPIO.input(self.key2)
        if last_state:
            return False
        else:
            # Wait for release
            while not GPIO.input(self.key2):
                time.sleep(0.02)
            # os.system('pkill mplayer') # This was specific, might be handled by caller
            return True

    #Upper left Button - Original press_c
    def press_upper_left(self):
        last_state=GPIO.input(self.key3)
        if last_state:
            return False
        else:
            # Wait for release
            while not GPIO.input(self.key3):
                time.sleep(0.02)
            return True

    #Upper Right Button - Original press_d
    def press_upper_right(self):
        last_state=GPIO.input(self.key4)
        if last_state:
            return False
        else:
            # Wait for release
            while not GPIO.input(self.key4):
                time.sleep(0.02)
            return True

if __name__ == '__main__':
    # Example usage:
    buttons = Button()
    print("Button test. Press buttons to see them detected. Press Ctrl+C to exit.")
    try:
        while True:
            if buttons.press_lower_right():
                print("Lower Right (A) pressed")
            if buttons.press_lower_left():
                print("Lower Left (B) pressed")
                # Example of how the caller might handle specific actions:
                # os.system('pkill mplayer')
            if buttons.press_upper_left():
                print("Upper Left (C) pressed")
            if buttons.press_upper_right():
                print("Upper Right (D) pressed")
            time.sleep(0.05) # Polling interval
    except KeyboardInterrupt:
        print("\nExiting button test.")
    finally:
        GPIO.cleanup()
