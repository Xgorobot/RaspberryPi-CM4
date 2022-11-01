from maix import display,image,gpio
from maix import event
import gc,os,time
#from select import select

print('show-----------------------------')

import pyaudio
import wave
import sys
import _thread
 
global exitmark
exitmark=0

gc.enable()
#image.load_freetype("msyh.ttc")
canvas = image.Image().new(size = (240, 240), color = (0, 0, 0), mode = "RGB")

pic_path = "/root/expression/"
_canvas_x, _canvas_y = 0, 0

def show(expression_name_cs, pic_num):
    global canvas
    for i in range(0, pic_num):
          canvas.clear()
          canvas.draw_image(image.Image().open(pic_path + expression_name_cs + "/" + str(i+1) + ".png"), _canvas_x, _canvas_y)
          display.show(canvas)
          time.sleep(0.3)

def play_show(threadName):
    while 1:
        show("sad", 8)
        show("naughty", 8)
        show("boring", 9)
        show("angry", 8)
        show("shame", 7)
        show("surprise", 8)
        show("happy", 6)
        show("sleepy", 8)
        show("drool", 8)
        show("pray", 8)
        show("hate", 10)
        show("love", 9)
        
def whick_key():
    global exitmark
    print('i am still here')
    from maix import event
    dev = event.InputDevice("/dev/input/event0")
    from select import select
    select([dev], [], [])
    for event in dev.read():
        #print(event)
        if event.code == 30:
            print(0)
        elif event.code == 48:
            print(1)
            exitmark=1
            #sys.exit()
        elif event.code == 105:
            print(2)
        elif event.code == 106:
            print(3)

def check_key(threadName):
    global exitmark
    while 1:
        if exitmark==1:
            break
        whick_key()
        time.sleep(0.01)
        
CHUNK = 1024
wf = wave.open(r"/root/music/dogshow.wav", 'rb')#(sys.argv[1], 'rb'
p = pyaudio.PyAudio()

def play_music(threadName):
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    
    data = wf.readframes(CHUNK)
    
    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

_thread.start_new_thread(check_key,("thread_check_key",))
_thread.start_new_thread(play_music,("thread_music",))
_thread.start_new_thread(play_show,("thread_show",))

while 1:
    if exitmark==1:
        sys.exit()
    pass
