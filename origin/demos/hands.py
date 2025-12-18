from uiutils import *
import numpy as np
from numpy import linalg
import cv2
import mediapipe as mp
import time

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

button = Button()
fm = get_dog_type_cache()
result = fm[0]
dog_type = result

dog.reset()
dogtime = 0

def finger_stretch_detect(point1, point2, point3):
    dist1 = np.linalg.norm((point2 - point1), ord=2)
    dist2 = np.linalg.norm((point3 - point1), ord=2)
    return 1 if dist2 > dist1 else 0

def detect_hands_gesture(result):
    gestures = {
        (1, 0, 0, 0, 0): "good",
        (0, 1, 0, 0, 0): "one",
        (0, 0, 1, 0, 0): "please civilization in testing",
        (0, 1, 1, 0, 0): "two",
        (0, 1, 1, 1, 0): "three",
        (0, 1, 1, 1, 1): "four",
        (1, 1, 1, 1, 1): "five",
        (1, 0, 0, 0, 1): "six",
        (0, 0, 1, 1, 1): "OK",
        (0, 0, 0, 0, 0): "stone"
    }
    return gestures.get(tuple(result), "NotInDetectRange")

IMAGE_FILES = []
with mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5) as hands:
    for idx, file in enumerate(IMAGE_FILES):
        image = cv2.flip(cv2.imread(file), 1)
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        print('Handedness:', results.multi_handedness)
        if not results.multi_hand_landmarks:
            continue
        image_height, image_width, _ = image.shape
        annotated_image = image.copy()
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
        cv2.imwrite(
            '/tmp/annotated_image' + str(idx) + '.png', cv2.flip(annotated_image, 1))
        if not results.multi_hand_world_landmarks:
            continue
        for hand_world_landmarks in results.multi_hand_world_landmarks:
            mp_drawing.plot_landmarks(
                hand_world_landmarks, mp_hands.HAND_CONNECTIONS, azimuth=5)

cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)

mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mpDraw = mp.solutions.drawing_utils
handLmsStyle = mpDraw.DrawingSpec(color=(0, 0, 255), thickness=2)
handConStyle = mpDraw.DrawingSpec(color=(0, 255, 0), thickness=2)

figure = np.zeros(5)
landmark = np.empty((21, 2))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Can not receive frame (stream end?). Exiting...")
        break

    frame_RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_RGB)
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    gesture_result = "NotInDetectRange"

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
                landmark[j, :] = landmark_

            for k in range(5):
                if k == 0:
                    figure_ = finger_stretch_detect(landmark[17], landmark[4 * k + 2], landmark[4 * k + 4])
                else:
                    figure_ = finger_stretch_detect(landmark[0], landmark[4 * k + 2], landmark[4 * k + 4])
                figure[k] = figure_
            gesture_result = detect_hands_gesture(figure)

    b, g, r = cv2.split(frame)
    frame = cv2.merge((r, g, b))
    frame = cv2.flip(frame, 1)

    if result.multi_hand_landmarks:
        cv2.putText(frame, f"{gesture_result}", (10, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 3)

    if time.time() > dogtime:
        print(fm[2])
        if gesture_result=="good":
          dogtime=time.time()
          dog.action(23)
          dogtime+=3
        elif gesture_result=="one":
          dogtime=time.time()
          dog.action(7)
          dogtime+=3
        elif gesture_result=="two":
          dogtime=time.time()
          dog.action(8)
          dogtime+=3
        elif gesture_result=="three":
          dogtime=time.time()
          dog.action(9)
          dogtime+=3
        elif gesture_result=="four":
          dogtime=time.time()
          dog.action(22)
          dogtime+=3
        elif gesture_result=="five":
          dogtime=time.time()
          dog.action(1)
          dogtime+=3
        elif gesture_result=="six":
          dogtime=time.time()
          dog.action(24)
          dogtime+=3
        elif gesture_result=="OK":
          dogtime=time.time()
          dog.action(19)
          dogtime+=3
        elif gesture_result=="stone":
          dogtime=time.time()
          dog.action(20)
          dogtime+=3

    imgok = Image.fromarray(frame)
    display.ShowImage(imgok)

    if cv2.waitKey(5) & 0xFF == 27:
        break
    if button.press_b():
        dog.reset()
        break

cap.release()
