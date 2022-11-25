import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import mediapipe as mp
from numpy import linalg
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
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


def finger_stretch_detect(point1, point2, point3):
    result = 0
    dist1 = np.linalg.norm((point2 - point1), ord=2)
    dist2 = np.linalg.norm((point3 - point1), ord=2)
    if dist2 > dist1:
        result = 1
    return result
    
def detect_hands_gesture(result):
    if (result[0] == 1) and (result[1] == 0) and (result[2] == 0) and (result[3] == 0) and (result[4] == 0):
        gesture = "good"
    elif (result[0] == 0) and (result[1] == 1)and (result[2] == 0) and (result[3] == 0) and (result[4] == 0):
        gesture = "one"
    elif (result[0] == 0) and (result[1] == 0)and (result[2] == 1) and (result[3] == 0) and (result[4] == 0):
        gesture = "please civilization in testing"
    elif (result[0] == 0) and (result[1] == 1)and (result[2] == 1) and (result[3] == 0) and (result[4] == 0):
        gesture = "two"
    elif (result[0] == 0) and (result[1] == 1)and (result[2] == 1) and (result[3] == 1) and (result[4] == 0):
        gesture = "three"
    elif (result[0] == 0) and (result[1] == 1)and (result[2] == 1) and (result[3] == 1) and (result[4] == 1):
        gesture = "four"
    elif (result[0] == 1) and (result[1] == 1)and (result[2] == 1) and (result[3] == 1) and (result[4] == 1):
        gesture = "five"
    elif (result[0] == 1) and (result[1] == 0)and (result[2] == 0) and (result[3] == 0) and (result[4] == 1):
        gesture = "six"
    elif (result[0] == 0) and (result[1] == 0)and (result[2] == 1) and (result[3] == 1) and (result[4] == 1):
        gesture = "OK"
    elif(result[0] == 0) and (result[1] == 0) and (result[2] == 0) and (result[3] == 0) and (result[4] == 0):
        gesture = "stone"
    else:
        gesture = "not in detect range..."
    
    return gesture



# For static images:
IMAGE_FILES = []
with mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5) as hands:
  for idx, file in enumerate(IMAGE_FILES):
    # Read an image, flip it around y-axis for correct handedness output (see
    # above).
    image = cv2.flip(cv2.imread(file), 1)
    # Convert the BGR image to RGB before processing.
    results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # Print handedness and draw hand landmarks on the image.
    print('Handedness:', results.multi_handedness)
    if not results.multi_hand_landmarks:
      continue
    image_height, image_width, _ = image.shape
    annotated_image = image.copy()
    for hand_landmarks in results.multi_hand_landmarks:
      #print('hand_landmarks:', hand_landmarks)
      '''
      print(
          f'Index finger tip coordinates: (',
          f'{hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * image_width}, '
          f'{hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * image_height})'
      )
      '''
      mp_drawing.draw_landmarks(
          annotated_image,
          hand_landmarks,
          mp_hands.HAND_CONNECTIONS,
          mp_drawing_styles.get_default_hand_landmarks_style(),
          mp_drawing_styles.get_default_hand_connections_style())

    cv2.imwrite(
        '/tmp/annotated_image' + str(idx) + '.png', cv2.flip(annotated_image, 1))
    # Draw hand world landmarks.
    if not results.multi_hand_world_landmarks:
      continue
    for hand_world_landmarks in results.multi_hand_world_landmarks:
      mp_drawing.plot_landmarks(
        hand_world_landmarks, mp_hands.HAND_CONNECTIONS, azimuth=5)

# For webcam input:
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils
handLmsStyle = mpDraw.DrawingSpec(color=(0, 0, 255), thickness=int(5))
handConStyle = mpDraw.DrawingSpec(color=(0, 255, 0), thickness=int(10))

figure = np.zeros(5)
landmark = np.empty((21, 2))


with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:
  while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Can not receive frame (stream end?). Exiting...")
        break
    frame_RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_RGB)
    frame_height = frame.shape[0]
    frame_width  = frame.shape[1]
    gesture_result=[]
    if result.multi_hand_landmarks:
        for i, handLms in enumerate(result.multi_hand_landmarks):
            mpDraw.draw_landmarks(frame, 
                                  handLms, 
                                  mpHands.HAND_CONNECTIONS,
                                  landmark_drawing_spec=handLmsStyle,
                                  connection_drawing_spec=handConStyle)

            for j, lm in enumerate(handLms.landmark):
                xPos = int(lm.x * frame_width)
                yPos = int(lm.y * frame_height)
                landmark_ = [xPos, yPos]
                landmark[j,:] = landmark_

            for k in range (5):
                if k == 0:
                    figure_ = finger_stretch_detect(landmark[17],landmark[4*k+2],landmark[4*k+4])
                else:    
                    figure_ = finger_stretch_detect(landmark[0],landmark[4*k+2],landmark[4*k+4])

                figure[k] = figure_
            #print(figure,'\n')

            gesture_result = detect_hands_gesture(figure)

    b,g,r = cv2.split(frame)
    frame = cv2.merge((r,g,b))
    frame = cv2.flip(frame, 1)
    if result.multi_hand_landmarks:
      cv2.putText(frame, f"{gesture_result}", (10,30), cv2.FONT_HERSHEY_COMPLEX, 1, (255 ,255, 0), 5)
    if gesture_result=="good":
      dog.action(14)
    elif gesture_result=="one":
      dog.action(7)
    elif gesture_result=="two":
      dog.action(8)
    elif gesture_result=="three":
      dog.action(9)
    elif gesture_result=="four":
      dog.action(10)
    elif gesture_result=="five":
      dog.action(1)
    elif gesture_result=="six":
      dog.action(16)
    elif gesture_result=="OK":
      dog.action(19)
    elif gesture_result=="stone":
      dog.action(12)
    
    imgok = Image.fromarray(frame)
    display.ShowImage(imgok)
    if cv2.waitKey(5) & 0xFF == 27:
      break
    if button.press_b():
      dog.reset()
      break
cap.release()