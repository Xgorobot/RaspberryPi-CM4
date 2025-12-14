import RPi.GPIO as GPIO
import time
import os

# Raspberry Pi GPIO model
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class Button:
    def __init__(self):
        self.key1 = 24 # Lower Right
        self.key2 = 23 # Lower Left
        self.key3 = 17 # Upper Left
        self.key4 = 22 # Upper Right

        # State flags
        self.adc_flag1 = False
        self.adc_flag2 = False
        self.adc_flag3 = False
        self.adc_flag4 = False

        GPIO.setup(self.key1, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.key2, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.key3, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self.key4, GPIO.IN, GPIO.PUD_UP)

        # Add event detect with debounce
        GPIO.add_event_detect(self.key1, GPIO.FALLING, callback=self.callback_key1, bouncetime=200)
        GPIO.add_event_detect(self.key2, GPIO.FALLING, callback=self.callback_key2, bouncetime=200)
        GPIO.add_event_detect(self.key3, GPIO.FALLING, callback=self.callback_key3, bouncetime=200)
        GPIO.add_event_detect(self.key4, GPIO.FALLING, callback=self.callback_key4, bouncetime=200)

    # Callbacks
    def callback_key1(self, channel): self.adc_flag1 = True
    def callback_key2(self, channel): self.adc_flag2 = True
    def callback_key3(self, channel): self.adc_flag3 = True
    def callback_key4(self, channel): self.adc_flag4 = True

    # Polling methods (Non-blocking, checks latch)
    def press_lower_right(self):
        if self.adc_flag1:
            self.adc_flag1 = False
            return True
        return False

    def press_lower_left(self):
        if self.adc_flag2:
            self.adc_flag2 = False
            return True
        return False

    def press_upper_left(self):
        if self.adc_flag3:
            self.adc_flag3 = False
            return True
        return False

    def press_upper_right(self):
        if self.adc_flag4:
            self.adc_flag4 = False
            return True
        return False

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
