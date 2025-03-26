import cv2
from uiutils import *
import numpy as np
import mediapipe as mp

button = Button()
cap = cv2.VideoCapture(0) 
cap.set(3, 320) 
cap.set(4, 240)
length=0
 
mpHands = mp.solutions.hands  
hands = mpHands.Hands(static_image_mode=False,
                      max_num_hands=1, 
                      min_detection_confidence=0.5, 
                      min_tracking_confidence=0.5) 
 
mpDraw = mp.solutions.drawing_utils
 
lmList = []

def handDetector(img):
    length=0
    results = hands.process(img)
    
    if results.multi_hand_landmarks: 
        for handlms in results.multi_hand_landmarks:
            for index, lm in enumerate(handlms.landmark):
                h, w, c = img.shape 
                cx ,cy =  int(lm.x * w), int(lm.y * h) 
                if index == 4:
                    x1, y1 = cx, cy    
                if index == 8:                    
                    x2, y2 = cx, cy
                    lmList.append([[x1,y1],[x2,y2]])
                    cv2.circle(img, (x1,y1), 5, (255,0,0), cv2.FILLED)
                    cv2.circle(img, (x2,y2), 5, (255,0,0), cv2.FILLED)
                    cv2.line(img, (x1,y1), (x2,y2), (255,0,255), 3)
                    cx, cy = (x1+x2)//2, (y1+y2)//2
                    cv2.circle(img, (cx,cy), 6, (255,0,0), cv2.FILLED)
                    length=(x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)**0.5
                    try:
                        length=int(length)
                    except:
                        length=0
    return img, lmList,length
while True:
    success, img = cap.read()
    if not success:
        break
    img, lmList ,length= handDetector(img)   
    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if length!=0:
        if length>1000:
            length=1000
        h=length/1000*40
        dog.translation('z', 75+h)
    else:
        dog.translation('z',95)
    if button.press_b():
        dog.reset()
        break 
cap.release()
