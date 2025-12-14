import RPi.GPIO as GPIO
import time

# Pin Definitions (from common/buttons.py)
KEY1 = 24 # Lower Right (Button A)
KEY2 = 23 # Lower Left (Button B)
KEY3 = 17 # Upper Left (Button C)
KEY4 = 22 # Upper Right (Button D)

GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Testing Buttons... Press Ctrl+C to exit.")
print(f"Pins: A={KEY1}, B={KEY2}, C={KEY3}, D={KEY4}")

try:
    while True:
        # Read states (0 = Pressed, 1 = Released because of Pull Up)
        val1 = GPIO.input(KEY1)
        val2 = GPIO.input(KEY2)
        val3 = GPIO.input(KEY3)
        val4 = GPIO.input(KEY4)

        status = []
        if val1 == 0: status.append("A (Lower Right)")
        if val2 == 0: status.append("B (Lower Left)")
        if val3 == 0: status.append("C (Upper Left)")
        if val4 == 0: status.append("D (Upper Right)")

        print(f"Reading... A:{val1} B:{val2} C:{val3} D:{val4}")
        
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    GPIO.cleanup()
