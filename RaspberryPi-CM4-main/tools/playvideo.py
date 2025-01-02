import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np
import threading

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

video_path = "./hotriver.mp4"
counter=0

def play_sound(a,b):
    time.sleep(0.1)  #音画速度同步了 但是时间轴可能不同步 这里调试一下
    os.system("sudo mplayer hotriver.mp4 -novideo")
    
x=threading.Thread(target=play_sound,args=(0,0))
x.start()

def PlayVideo(video_path):
    global counter
    video=cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS) 
    print(fps)
    init_time=time.time()
    while True:
        grabbed, dst = video.read()
        #dst = cv2.resize(frame, (320, 240))
        #if not grabbed:
            #print("End of video")
            #break
        b,g,r = cv2.split(dst)
        dst = cv2.merge((r,g,b))
        imgok = Image.fromarray(dst)
        display.ShowImage(imgok)
        #强制卡帧数 实测帧数不要超过20贞 否则显示跟不上 但是20贞转换经常有问题 所以建议直接15贞
        counter += 1
        ctime=time.time()- init_time
        if ctime != 0:
            qtime=counter/fps-ctime
            print(qtime)
            if qtime>0:
                time.sleep(qtime)




    video.release()
    cv2.destroyAllWindows()

PlayVideo(video_path)


