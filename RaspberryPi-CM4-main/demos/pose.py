import mediapipe as mp
import numpy as np
mp_pose = mp.solutions.pose
import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import threading
from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()
#-----------------------COMMON INIT-----------------------
mppose = mp.solutions.pose
mpdraw = mp.solutions.drawing_utils
poses = mppose.Pose()
h = 0
w = 0

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

start_time = 0
status = False

sport = {
    "name": "Squat",
    "count": 0,
    "calories": 0
}
height=115
quitmark=0
def mode(num):
    global height,quitmark
    while quitmark==0:
        dog.translation('z',height)
        time.sleep(0.1)
    

mode_button = threading.Thread(target=mode, args=(0,))
mode_button.start()


def logger(count, cals):
    f = open("log.txt", 'a')
    fs = f"{time.ctime()} count: {count} cals: {cals}\n"
    f.write(fs)
    f.close()


def calc_angles(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])

    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle


def get_landmark(landmarks, part_name):
    return [
        landmarks[mppose.PoseLandmark[part_name].value].x,
        landmarks[mppose.PoseLandmark[part_name].value].y,
        landmarks[mppose.PoseLandmark[part_name].value].z,
    ]


def get_visibility(landmarks):
    if landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].visibility < 0.8 or \
            landmarks[mppose.PoseLandmark["LEFT_HIP"].value].visibility < 0.8:
        return False
    else:
        return True


def get_body_ratio(landmarks):
    r_body = abs(landmarks[mppose.PoseLandmark["RIGHT_SHOULDER"].value].y
                 - landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].y)
    l_body = abs(landmarks[mppose.PoseLandmark["LEFT_SHOULDER"].value].y
                 - landmarks[mppose.PoseLandmark["LEFT_HIP"].value].y)
    avg_body = (r_body + l_body) / 2
    r_leg = abs(landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].y
                - landmarks[mppose.PoseLandmark["RIGHT_ANKLE"].value].y)
    l_leg = abs(landmarks[mppose.PoseLandmark["LEFT_HIP"].value].y
                - landmarks[mppose.PoseLandmark["LEFT_ANKLE"].value].y)
    if r_leg > l_leg:
        return r_leg / avg_body
    else:
        return l_leg / avg_body


def get_knee_angle(landmarks):
    r_hip = get_landmark(landmarks, "RIGHT_HIP")
    l_hip = get_landmark(landmarks, "LEFT_HIP")

    r_knee = get_landmark(landmarks, "RIGHT_KNEE")
    l_knee = get_landmark(landmarks, "LEFT_KNEE")

    r_ankle = get_landmark(landmarks, "RIGHT_ANKLE")
    l_ankle = get_landmark(landmarks, "LEFT_ANKLE")

    r_angle = calc_angles(r_hip, r_knee, r_ankle)
    l_angle = calc_angles(l_hip, l_knee, l_ankle)

    m_hip = (r_hip + l_hip)
    m_hip = [x / 2 for x in m_hip]
    m_knee = (r_knee + l_knee)
    m_knee = [x / 2 for x in m_knee]
    m_ankle = (r_ankle + l_ankle)
    m_ankle = [x / 2 for x in m_ankle]

    mid_angle = calc_angles(m_hip, m_knee, m_ankle)

    return [r_angle, l_angle, mid_angle]

def main():
    global h, w, start_time, status,height,quitmark
    flag = False
    if not cap.isOpened():
        print("Camera not open")
        exit()

    tmp = f"a{sport['count']}\n"
    #ser.write(str.encode(tmp))
    tmp = f"b{sport['calories']}\n"
    #ser.write(str.encode(tmp))

    while not flag:
        ret, frame = cap.read()
        if not ret:
            print("Read Error")
            break
        frame = cv2.flip(frame, 1)
        rgbframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        poseoutput = poses.process(rgbframe)
        h, w, _ = frame.shape
        preview = frame.copy()

        if poseoutput.pose_landmarks:
            mpdraw.draw_landmarks(preview, poseoutput.pose_landmarks, mppose.POSE_CONNECTIONS)
            knee_angles = get_knee_angle(poseoutput.pose_landmarks.landmark)
            body_ratio = get_body_ratio(poseoutput.pose_landmarks.landmark)
            # if knee_angles[0] < 120:
            #     cv2.putText(preview, "Left: Down {:.1f}".format(knee_angles[0]), (10, 40)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA
            #                 )
            # elif knee_angles[0] < 130:
            #     cv2.putText(preview, "Left: ??? {:.1f}".format(knee_angles[0]), (10, 40)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA
            #                 )
            # else:
            #     cv2.putText(preview, "Left: Up {:.1f}".format(knee_angles[0]), (10, 40)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA
            #                 )

            # if knee_angles[1] < 120:
            #     cv2.putText(preview, "Right: Down {:.1f}".format(knee_angles[1]), (10, 80)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA
            #                 )
            # elif knee_angles[1] < 130:
            #     cv2.putText(preview, "Right: ??? {:.1f}".format(knee_angles[1]), (10, 80)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA
            #                 )
            # else:
            #     cv2.putText(preview, "Right: Up {:.1f}".format(knee_angles[1]), (10, 80)
            #                 , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA
            #                 )

            avg_angle = (knee_angles[0] + knee_angles[1]) // 2

            #determine the status
            if status:
                if avg_angle > 160:
                    status = False
                    pass_time = time.time() - start_time
                    start_time = 0
                    if 3000 > pass_time > 3:
                        sport['count'] = sport['count'] + 1
                        sport['calories'] = sport['calories'] + int(0.66 * pass_time)
                        logger(sport['count'], sport['calories'])
                        tmp = f"a{sport['count']}\n"
                        tmp = f"b{sport['calories']}\n"

            else:
                if avg_angle < 120 and body_ratio < 1.2:
                    start_time = time.time()
                    status = True
            height=int(115-(180-avg_angle)/90*40)
            print(avg_angle,height)

            if status:
                cv2.putText(preview, f"{height} : {avg_angle:.1f} {body_ratio:.3f}", (10, 40)
                            , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA
                            )
            else:
                cv2.putText(preview, f"{height} : {avg_angle:.1f} {body_ratio:.3f}", (10, 40)
                            , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA
                            )
        else:
            start_time = 0
            #dog.reset()
        b,g,r = cv2.split(preview)
        image = cv2.merge((r,g,b))
        #image = cv2.flip(image, 1)
        imgok = Image.fromarray(image)
        display.ShowImage(imgok)
        if cv2.waitKey(5) & 0xFF == 27:
            break
        if button.press_b():
            dog.reset()
            break

    # release camera
    cap.release()
    quitmark=True
    dog.reset()

main()



