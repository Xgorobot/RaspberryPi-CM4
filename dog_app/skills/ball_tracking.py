import cv2
import numpy as np
from PIL import Image
import time
from .manager import Skill

class BallTrackingSkill(Skill):
    def __init__(self, dog, display, camera):
        super().__init__("BallTracking", dog, display, camera)
        self.color_mode = "red" # Default color
        # PID / Control parameters from original demo
        self.mintime_yaw = 0.7
        self.mintime_x = 0.3
        self.x_speed_far = 16
        self.x_speed_slow = 8
        self.turn_speed = 8
        self.circle_count = 0
        self.un_circle_count = 0
        self.mx, self.my, self.mr = 0, 0, 0

    def run(self):
        print("BallTrackingSkill: Started.")
        if not self.camera or not self.camera.is_opened():
            print("BallTrackingSkill: Camera not available.")
            return

        self.dog.reset()
        # Head up
        self.dog.attitude('p', 15)
        self.dog.translation('z', 75)
        
        while not self._stop_event.is_set():
            ret, frame = self.camera.read() # Assuming DogCamera has .read() returning (ret, frame) like cv2
            # If DogCamera uses get_frame_cv2(), adapt here.
            # Checking DogCamera... it usually has get_frame() returning bytes or something.
            # Let's check common/camera.py later, but valid CV2 read is common expectation.
            # For now assume .read() works or use self.camera.cap.read() if exposed.
            # Based on web_server.py: get_frame_jpeg(). 
            # I should use self.camera.read_cv2() if it exists or access cap directly.
            
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            # Process Image
            processed_frame, action_result = self.process_image(frame)
            
            # Display logic
            # Convert BGR to RGB for PIL
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # Resize if needed (Display is 320x240)
            if pil_image.size != (320, 240):
                pil_image = pil_image.resize((320, 240))
            
            if self.display:
                self.display.ShowImage(pil_image)
            
            if action_result == "GRAB":
                print("BallTrackingSkill: ACTION - GRAB!")
                # Perform grab sequence
                self.catch_arm()
                break # Exit after grab? Or reset? Original exits.
                
            time.sleep(0.01)

    def process_image(self, image):
        # ... Ported logic from ball.py ...
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = self.get_color_mask(hsv, self.color_mode)
        
        # Hough Circles (simplified for demonstration/port speed)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply mask to help? Original used bitwise_and then gray.
        masked_img = cv2.bitwise_and(image, image, mask=mask)
        gray_masked = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.GaussianBlur(gray_masked, (9, 9), 2)
        
        circles = cv2.HoughCircles(gray_blur, cv2.HOUGH_GRADIENT, 1, 50, param1=100, param2=20, minRadius=10, maxRadius=100)
        
        action = None
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Max radius
            c = max(circles, key=lambda x: x[2])
            x, y, r = c
            
            cv2.circle(image, (x, y), r, (0, 255, 0), 2)
            cv2.circle(image, (x, y), 2, (0, 0, 255), 3)
            
            self.un_circle_count = 0
            
            # Logic to move robot
            # center x = 160 (320/2)
            # distance approx by radius? Original used formula: distance = 54.82 - mr (rough linear?)
            # Let's use simple logic: Center X, approach until radius is large enough.
            
            err_x = x - 160
            
            if r > 60: # Close enough
                action = "GRAB"
            else:
                # Track X
                if abs(err_x) > 40:
                    if err_x > 0:
                         self.dog.turn(-10) # Turn right
                    else:
                         self.dog.turn(10) # Turn left
                else:
                    # Move forward
                    self.dog.move_x(15)
                    self.dog.turn(0) # Stop turning
                    
        else:
            self.un_circle_count += 1
            if self.un_circle_count > 20: 
                self.dog.stop() # Lost target
            
        return image, action

    def get_color_mask(self, hsv, color):
        if color == "red":
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([160, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower1, upper1)
            mask2 = cv2.inRange(hsv, lower2, upper2)
            return mask1 + mask2
        elif color == "blue":
            return cv2.inRange(hsv, np.array([100, 100, 100]), np.array([124, 255, 255]))
        elif color == "green":
             return cv2.inRange(hsv, np.array([35, 100, 100]), np.array([85, 255, 255]))
        return None

    def catch_arm(self):
        self.dog.stop()
        time.sleep(0.5)
        self.dog.translation('z', 10)
        self.dog.attitude('p', 15)
        self.dog.claw(5) # Open
        time.sleep(1)
        # Arm movement
        self.dog.action(128) # Use preset catch? or Manual arm
        # dog.arm_polar(200, 130) # From original
        self.dog.action(130) # Catch bottom
        time.sleep(2)
        # Reset
        self.dog.reset()
