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
import cv2
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

def calculate_angle(a,b,c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle >180.0:
        angle = 360-angle
    return angle

#angel
angle_min = []
angle_min_hip = []
cap = cv2.VideoCapture(0)

# Curl counter variables
counter = 0 
min_ang = 0
max_ang = 0
min_ang_hip = 0
max_ang_hip = 0
stage = None
width = 320
height = 240
cap.set(3,320)
cap.set(4,240)

up_mark=False
down_mark=False

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        # Make detection
        results = pose.process(image)
        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark
            # Get coordinates
            shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            """elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            """
            # Get coordinates
            hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            print(hip,knee,ankle)

            # Calculate angle
            #angle = calculate_angle(shoulder, elbow, wrist)
            angle_knee = calculate_angle(hip, knee, ankle) #Knee joint angle
            print(angle_knee)
            angle_knee = round(angle_knee,2)
            angle_hip = calculate_angle(shoulder, hip, knee)
            angle_hip = round(angle_hip,2)
            hip_angle = 180-angle_hip
            knee_angle = 180-angle_knee
            angle_min.append(angle_knee)
            angle_min_hip.append(angle_hip)
            

            if angle_knee > 169:
                stage = "up"
                if not up_mark:
                    dog.translation('z',75)
                    up_mark=True
                    down_mark=False
            if angle_knee <= 90 and stage =='up':
                stage="down"
                counter +=1
                print(counter)
                min_ang  =min(angle_min)
                max_ang = max(angle_min)
                
                min_ang_hip  =min(angle_min_hip)
                max_ang_hip = max(angle_min_hip)
                
                print(min(angle_min), " _ ", max(angle_min))
                print(min(angle_min_hip), " _ ", max(angle_min_hip))
                angle_min = []
                angle_min_hip = []
                if not down_mark:
                    dog.translation('z',75)
                    up_mark=False
                    down_mark=True
        except:
            pass
        
        
        # Rep data
        """cv2.putText(image, 'REPS', (15,12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)"""
        cv2.putText(image, "Repetition:" + str(counter), 
                    (10,20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)
        print(counter)
        
        # Stage data
        """cv2.putText(image, 'STAGE', (65,12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)"""
        """cv2.putText(image, stage, 
                    (10,120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)"""
        
        #Knee angle:
        """cv2.putText(image, 'Angle', (65,12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)"""
        cv2.putText(image, "Knee-joint: " + str(min_ang), 
                    (10,40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)
        
        #Hip angle:
        cv2.putText(image, "Hip-joint: " + str(min_ang_hip), 
                    (10,60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)
        

        
        
        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(0,0,0), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(203,17,17), thickness=2, circle_radius=2) 
                                 )               
        
        #out.write(image)

        b,g,r = cv2.split(image)
        image = cv2.merge((r,g,b))
        #image = cv2.flip(image, 1)
        imgok = Image.fromarray(image)
        display.ShowImage(imgok)
        if button.press_b():
            dog.reset()
            break
    dog.reset()
    cap.release()
