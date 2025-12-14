import sys
import time
import os

# Ensure we can import xgolib
sys.path.append(os.path.expanduser('~/dog_app'))
try:
    from control.xgolib import XGO
except ImportError:
    # Fallback if path is different
    sys.path.append('/home/jinliang/dog_app')
    from control.xgolib import XGO

print("Initializing XGO...")
try:
    dog = XGO(port='/dev/ttyAMA0', version='cm4')
    print("XGO Verified.")
except Exception as e:
    print(f"Failed to init XGO: {e}")
    sys.exit(1)

print("--- DEBUG START ---")
print("1. Sending load_allmotor()...")
dog.load_allmotor()

print("2. Sleeping 1.5s...")
time.sleep(1.5)

print("3. Sending reset()...")
dog.reset()

print("4. Sleeping 1.0s...")
time.sleep(1.0)

print("5. Sending action(2) [Stand]...")
dog.action(2)

print("--- DEBUG END ---")
