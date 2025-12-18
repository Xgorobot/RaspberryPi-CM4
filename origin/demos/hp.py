import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from uiutils import *

button = Button()

# Initialize OpenCV camera capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

mpHands = mp.solutions.hands  
hands = mpHands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def handDetector(img):
    length = 0
  
    results = hands.process(img)
    
    if results.multi_hand_landmarks:
        for handlms in results.multi_hand_landmarks:
            for index, lm in enumerate(handlms.landmark):
                h, w = img.shape[:2]
                cx, cy = int(lm.x * w), int(lm.y * h)
                if index == 4:
                    x1, y1 = cx, cy
                if index == 8:
                    x2, y2 = cx, cy
                  
                    cv2.circle(img, (x1,y1), 5, (0,0,255), cv2.FILLED) 
                    cv2.circle(img, (x2,y2), 5, (0,0,255), cv2.FILLED) 
                    cv2.line(img, (x1,y1), (x2,y2), (255,0,255), 3) 
                    length = ((x1-x2)**2 + (y1-y2)**2)**0.5
                    length = min(int(length), 1000)
    return img, length

while True:
    ret, img = cap.read()
    if not ret:
        break
        
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB for processing
    img, length = handDetector(img)
    img = cv2.flip(img, 1)
    img_pil = Image.fromarray(img)
    display.ShowImage(img_pil)
    
    print(f"Detected finger distance: {length}")
    
    if length > 0:
        h = min(max(length, 0), 100)
        target_height = 75 + (h / 100 * 40)
        dog.translation('z', target_height)
        print(f"Setting height to: {target_height}")
    else:
        dog.translation('z', 95)
        
    if button.press_b():
        dog.reset()
        break

cap.release()