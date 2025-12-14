from control.xgolib import init_dog
import time

dog, _, _ = init_dog()
if not dog:
    print("Failed to init dog")
    exit(1)

print("Starting Action 1 (Lie Down)...")
dog.action(1)

# Wait for "bottom" position
time.sleep(1.8)

# Capture Pose
print("Capturing Motor Angles...")
angles = dog.read_motor()
print(f"CAPTURED_ANGLES: {angles}")

# Unload safety
dog.unload_allmotor()
print("Done.")
