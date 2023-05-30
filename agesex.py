import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from subprocess import Popen
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0',version="xgolite")
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"white")
display.ShowImage(splash)
draw = ImageDraw.Draw(splash)
button=Button()
#-*- coding: utf-8 -*-
import cv2 as cv
import time

pic_path = "./expression/"
_canvas_x, _canvas_y = 0, 0

def show(expression_name_cs, pic_num):
    global canvas
    for i in range(0, pic_num):
        filename=pic_path + expression_name_cs + "/" + str(i+1) + ".png"
        exp = Image.open(pic_path + expression_name_cs + "/" + str(i+1) + ".png")
        display.ShowImage(exp)
        time.sleep(0.05)
        if button.press_b():
          sys.exit()

def getFaceBox(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    net.setInput(blob)
    detections = net.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            bboxes.append([x1, y1, x2, y2]) 
            cv.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)),8)
    return frameOpencvDnn, bboxes

faceProto = "opencv_face_detector.pbtxt"
faceModel = "opencv_face_detector_uint8.pb"

ageProto = "age_deploy.prototxt"
ageModel = "age_net.caffemodel"

genderProto = "gender_deploy.prototxt"
genderModel = "gender_net.caffemodel"

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

ageNet = cv.dnn.readNet(ageModel, ageProto)
genderNet = cv.dnn.readNet(genderModel, genderProto)
faceNet = cv.dnn.readNet(faceModel, faceProto)

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
padding = 20
man=0
women=0
while 1:
    t = time.time()
    hasFrame, frame = cap.read()
    frame = cv.flip(frame, 1)
    if not hasFrame:
        cv.waitKey()
        break
    frameFace, bboxes = getFaceBox(faceNet, frame)
    if not bboxes:
        print("No face Detected, Checking next frame")
    gender=''
    age=''
    for bbox in bboxes:
        face = frame[max(0, bbox[1] - padding):min(bbox[3] + padding, frame.shape[0] - 1),
               max(0, bbox[0] - padding):min(bbox[2] + padding, frame.shape[1] - 1)]
        blob = cv.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        genderNet.setInput(blob)
        genderPreds = genderNet.forward()
        gender = genderList[genderPreds[0].argmax()]
        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]
        label = "{},{}".format(gender, age) 
        cv.putText(frameFace, label, (bbox[0], bbox[1] - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2,
                   cv.LINE_AA)  
    b,g,r = cv2.split(frameFace)
    frameFace = cv2.merge((r,g,b))
    imgok = Image.fromarray(frameFace)
    display.ShowImage(imgok)
    if gender!='':
      if gender=='Male':
        man+=1
        women=0
        if man>3:
          proc=Popen(['mplayer','hate.mp3'])
          show("angry", 8)
          dog.action(15)
          man=0
          time.sleep(2)
      if gender=='Female':
        women+=1
        man=0
        if women>3:
          proc=Popen(['mplayer','happy.wav'])
          show("happy", 6)
          dog.action(16)
          women=0
          time.sleep(2)
      hasFrame, frame = cap.read()
      frame = cv.flip(frame, 1)
    if button.press_b():
        dog.reset()
        break
