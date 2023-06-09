from subprocess import Popen
import _thread
#import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
from xgolib import XGO
import os
import _thread as thread
import signal


display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"white")
display.ShowImage(splash)
draw = ImageDraw.Draw(splash)
button=Button()
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
font = ImageFont.truetype("msyh.ttc",40)
#-----------------------COMMON INIT----------------------- 
boardcast=False
exitmark=False


pic_path = "./expression/"
_canvas_x, _canvas_y = 0, 0

def display_cjk_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = font_size) 

def show(expression_name_cs, pic_num):
    global canvas,playmark,exitmark,boardcast
    for i in range(0, pic_num):
        if playmark==True and exitmark==False and boardcast==True:
            filename=pic_path + expression_name_cs + "/" + str(i+1) + ".png"
            exp = Image.open(pic_path + expression_name_cs + "/" + str(i+1) + ".png")
            display.ShowImage(exp)
            time.sleep(0.05)
        

from socket import *
address = ('', 6001)
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
s.bind(address)

def broadcast_check(*args):
    global boardcast,playmark
    while 1:
        data, address = s.recvfrom(128)
        if data==b'1':
            print('broadcast 1')
            boardcast=True
        elif data==b'0':
            print('broadcast 0')
            boardcast=False
            playmark=False
        if exitmark==True:
            break
def button_check(*args):
    global exitmark
    while 1:
        if button.press_b():
            dog.perform(0)  
            sys.exit()
            exitmark=True
            break

thread.start_new_thread(broadcast_check, ())
thread.start_new_thread(button_check, ())

playmark=False
while 1:
    print(boardcast)
    if exitmark==False:
      if boardcast:
          print('playmark:')
          print(playmark)
          if not playmark:
              playmark=True
              dog.perform(1)  
              proc=Popen("mplayer dog.mp3", shell=True,preexec_fn=os.setsid) 
              while 1:
                  if playmark==False or boardcast==False or exitmark==True:
                      break
                  show("sad", 14)
                  show("naughty", 14)
                  show("boring", 14)
                  show("angry", 13)
                  show("shame", 11)
                  show("surprise", 15)
                  show("happy", 12)
                  show("sleepy", 19)
                  show("seek", 12)
                  show("lookaround", 12)
                  show("love", 13)
      else:
          try:
              proc.terminate()
              proc.wait()
              os.killpg(proc.pid,signal.SIGTERM)
              print('kill music')
          except:
              print('no music play')
          dog.perform(0)
          print('ready...')
          splash = Image.new("RGB", (display.height, display.width ),"black")
          draw = ImageDraw.Draw(splash)
          draw.text((100,95),'READY',fill =(255,255,255),font = font) 
          display.ShowImage(splash)
    if button.press_b() or exitmark==True:
        exitmark=True
        try:
            proc=Popen("mplayer dog.mp3", shell=True) 
            proc.terminate()
            proc.kill()
        except:
            pass
        dog.reset()  
        sys.exit()

