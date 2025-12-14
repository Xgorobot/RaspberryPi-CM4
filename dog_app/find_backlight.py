
import RPi.GPIO as GPIO
import time

# Pin Candidates
PINS = [18, 22, 23, 24, 21, 13, 19, 5, 6]
NAMES = ["18 (Std)", "22", "23", "24", "21", "13 (PWM)", "19 (PWM)", "5", "6"]

def test_pin(pin, name, index):
    print(f"[{index+1}/{len(PINS)}] Testing GPIO {pin} ({name})...")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        
        # Turn OFF (Low) for 3 seconds
        print(f"   -> OFF (Low) for 2s")
        GPIO.output(pin, GPIO.LOW)
        time.sleep(2.0)
        
        # Turn ON (High)
        print(f"   -> ON (High)")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    GPIO.setwarnings(False)
    print("------------------------------------------------")
    print("SLOW BACKLIGHT TEST - Watch the screen!")
    print("I will turn off potential backlight pins one by one.")
    print("Please note WHICH number makes the screen go BLACK.")
    print("------------------------------------------------")
    time.sleep(2)
    
    for i, p in enumerate(PINS):
        test_pin(p, NAMES[i], i)
        
    print("------------------------------------------------")
    print("Test Complete.")
    GPIO.cleanup()
