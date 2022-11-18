import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from subprocess import Popen

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"white")
display.ShowImage(splash)
draw = ImageDraw.Draw(splash)
button=Button()
#-----------------------COMMON INIT-----------------------
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
        splash.paste(exp,(40,0))
        #canvas.draw_image(image.Image().open(pic_path + expression_name_cs + "/" + str(i+1) + ".png"), _canvas_x, _canvas_y)
        display.ShowImage(splash)
        time.sleep(0.05)
        if button.press_b():
          sys.exit()


# 检测人脸并绘制人脸bounding box
def getFaceBox(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]  # 高就是矩阵有多少行
    frameWidth = frameOpencvDnn.shape[1]  # 宽就是矩阵有多少列
    blob = cv.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)
    #  blobFromImage(image[, scalefactor[, size[, mean[, swapRB[, crop[, ddepth]]]]]]) -> retval  返回值   # swapRB是交换第一个和最后一个通道   返回按NCHW尺寸顺序排列的4 Mat值
    net.setInput(blob)
    detections = net.forward()  # 网络进行前向传播，检测人脸
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            bboxes.append([x1, y1, x2, y2])  # bounding box 的坐标
            cv.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight / 150)),
                         8)  # rectangle(img, pt1, pt2, color[, thickness[, lineType[, shift]]]) -> img
    return frameOpencvDnn, bboxes


# 网络模型  和  预训练模型
faceProto = "opencv_face_detector.pbtxt"
faceModel = "opencv_face_detector_uint8.pb"

ageProto = "age_deploy.prototxt"
ageModel = "age_net.caffemodel"

genderProto = "gender_deploy.prototxt"
genderModel = "gender_net.caffemodel"

# 模型均值
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
genderList = ['Male', 'Female']

# 加载网络
ageNet = cv.dnn.readNet(ageModel, ageProto)
genderNet = cv.dnn.readNet(genderModel, genderProto)
# 人脸检测的网络和模型
faceNet = cv.dnn.readNet(faceModel, faceProto)

# 打开一个视频文件或一张图片或一个摄像头
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
padding = 20
man=0
women=0
while 1:
    # Read frame
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
        # print(bbox)   # 取出box框住的脸部进行检测,返回的是脸部图片
        face = frame[max(0, bbox[1] - padding):min(bbox[3] + padding, frame.shape[0] - 1),
               max(0, bbox[0] - padding):min(bbox[2] + padding, frame.shape[1] - 1)]
        #print("=======", type(face), face.shape)  #  <class 'numpy.ndarray'> (166, 154, 3)
        #
        blob = cv.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        #print("======", type(blob), blob.shape)  # <class 'numpy.ndarray'> (1, 3, 227, 227)
        genderNet.setInput(blob)   # blob输入网络进行性别的检测
        genderPreds = genderNet.forward()   # 性别检测进行前向传播
        #print("++++++", type(genderPreds), genderPreds.shape, genderPreds)   # <class 'numpy.ndarray'> (1, 2)  [[9.9999917e-01 8.6268375e-07]]  变化
        gender = genderList[genderPreds[0].argmax()]   # 分类  返回性别类型
        # print("Gender Output : {}".format(genderPreds))
        #print("Gender : {}, conf = {:.3f}".format(gender, genderPreds[0].max()))

        ageNet.setInput(blob)
        agePreds = ageNet.forward()
        age = ageList[agePreds[0].argmax()]
        #print(agePreds[0].argmax())  # 3
        #print("*********", agePreds[0])   #  [4.5557402e-07 1.9009208e-06 2.8783199e-04 9.9841607e-01 1.5261240e-04 1.0924522e-03 1.3928890e-05 3.4708322e-05]
        #print("Age Output : {}".format(agePreds))
        #print("Age : {}, conf = {:.3f}".format(age, agePreds[0].max()))

        label = "{},{}".format(gender, age)
        
        cv.putText(frameFace, label, (bbox[0], bbox[1] - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2,
                   cv.LINE_AA)  # putText(img, text, org, fontFace, fontScale, color[, thickness[, lineType[, bottomLeftOrigin]]]) -> img
    #cv.imshow("Age Gender Demo", frameFace)
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
          man=0
<<<<<<< HEAD
          time.sleep(2)
=======
>>>>>>> 7754f99b7d5c3348c178b224e6df1064220a513d
      if gender=='Female':
        women+=1
        man=0
        if women>3:
          proc=Popen(['mplayer','happy.wav'])
          show("happy", 6)
          women=0
<<<<<<< HEAD
          time.sleep(2)
=======
>>>>>>> 7754f99b7d5c3348c178b224e6df1064220a513d
      hasFrame, frame = cap.read()
      frame = cv.flip(frame, 1)
    if button.press_b():
        dog.reset()
        break
    #print("time : {:.3f} ms".format(time.time() - t))
