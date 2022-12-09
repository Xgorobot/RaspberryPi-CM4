import mediapipe as mp
import numpy as np
mp_pose = mp.solutions.pose
import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()
#-----------------------COMMON INIT-----------------------
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic
joint_list = [[24,26,28], [23,25,27], [14,12,24], [13,11,23]]  # leg&arm

# For webcam input:
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      # If loading a video, use 'break' instead of 'continue'.
      continue

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    # Draw the pose annotation on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    # Flip the image horizontally for a selfie-view display.
    
    if results.pose_landmarks:
        RHL = results.pose_landmarks
        angellist=[]
        for joint in joint_list:
            a = np.array([RHL.landmark[joint[0]].x, RHL.landmark[joint[0]].y])
            b = np.array([RHL.landmark[joint[1]].x, RHL.landmark[joint[1]].y])
            c = np.array([RHL.landmark[joint[2]].x, RHL.landmark[joint[2]].y])
            radians_fingers = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
            angle = np.abs(radians_fingers * 180.0 / np.pi) 
            if angle > 180.0:
                angle = 360 - angle
            #cv2.putText(image, str(round(angle, 2)), tuple(np.multiply(b, [640, 480]).astype(int)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            angellist.append(angle)
    else:
        angellist=[]
        dog.reset()
    print(angellist)
    b,g,r = cv2.split(image)
    image = cv2.merge((r,g,b))
    image = cv2.flip(image, 1)
    try:
        res=str(int(angellist[0]))+'|'+str(int(angellist[1]))+'|'+str(int(angellist[2]))+'|'+str(int(angellist[3]))
        dog.leg(1,[0,-18+int(angellist[2]/10),0])
        dog.leg(2,[0,-18+int(angellist[3]/10),0])
    except:
        res=' '
    cv2.putText(image,res,(10,220),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)
    #cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
    if cv2.waitKey(5) & 0xFF == 27:
        break
    if button.press_b():
        dog.reset()
        break
    
cap.release()