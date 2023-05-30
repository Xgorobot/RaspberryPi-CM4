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

#-----------------------COMMON INIT-----------------------
from keras.models import load_model
from time import sleep
from tensorflow.keras.utils import img_to_array
from keras.preprocessing import image
import cv2
import numpy as np

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


face_classifier=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
classifier = load_model('EmotionDetectionModel.h5')

class_labels=['Angry','Happy','Neutral','Sad','Surprise']

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
angry=0
happy=0
sad=0
surprise=0

while True:
    ret,frame=cap.read()
    labels=[]
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=face_classifier.detectMultiScale(gray,1.3,5)
    label=''
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray=gray[y:y+h,x:x+w]
        roi_gray=cv2.resize(roi_gray,(48,48),interpolation=cv2.INTER_AREA)

        if np.sum([roi_gray])!=0:
            roi=roi_gray.astype('float')/255.0
            roi=img_to_array(roi)
            roi=np.expand_dims(roi,axis=0)

            preds=classifier.predict(roi)[0]
            label=class_labels[preds.argmax()]
            print(label)
            label_position=(x,y)
        else:
            pass
    
    b,g,r = cv2.split(frame)
    frame = cv2.merge((r,g,b))
    frame = cv2.flip(frame, 1)
    try:
        cv2.putText(frame,label,label_position,cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),3)
    except:
        pass
    imgok = Image.fromarray(frame)
    display.ShowImage(imgok)
    if label!='':
      time.sleep(1)
      if label=='Angry':
        angry+=1
        happy=0
        sad=0
        surprise=0
        if angry>2:
          dog.action(24)
          proc=Popen(['mplayer','hate.mp3'])
          show("angry", 8)
          angry=0
          time.sleep(7)
      if label=='Happy':
        angry=0
        happy+=1
        sad=0
        surprise=0
        if happy>2:
          dog.action(24)
          proc=Popen(['mplayer','happy.wav'])
          show("happy", 6)
          happy=0
          time.sleep(7)
      if label=='Sad':
        angry=0
        happy=0
        sad+=1
        surprise=0
        if sad>2:
          dog.action(24)
          proc=Popen(['mplayer','sad.wav'])
          show("sad", 8)
          sad=0
          time.sleep(7)
      if label=='Surprise':
        angry==0
        happy=0
        sad=0
        surprise+=1
        if surprise>2:
          dog.action(24)
          proc=Popen(['mplayer','surprise.wav'])
          show("surprise", 8)
          surprise=0
          time.sleep(7)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if button.press_b():
        dog.reset()
        break
cap.release()
cv2.destroyAllWindows()
