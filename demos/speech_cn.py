import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time 
import time as tttime
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

import sys
import signal
from xgolib import XGO
import time
import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import threading

import pyaudio
import wave

import numpy as np
from scipy import fftpack

quitmark=0
button=Button()

def action(num):
    global quitmark
    while quitmark==0:
        time.sleep(0.01)
        if button.press_b():
            quitmark=1

check_button = threading.Thread(target=action, args=(0,))
check_button.start()

STATUS_FIRST_FRAME = 0  
STATUS_CONTINUE_FRAME = 1  
STATUS_LAST_FRAME = 2
xunfei=''  


class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }

        url = url + '?' + urlencode(v)
        return url

def on_message(ws, message):
    global xunfei
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            result=json.dumps(data, ensure_ascii=False)
            tx=''
            for r in data:
                tx+=r['cw'][0]['w']
            xunfei+=tx

            #textshow=sid.split(" ")[1]


    except Exception as e:
        print("receive msg,but parse exception:", e)


def on_error(ws, error):
    print("### error:", error)

def on_close(ws,t,x):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        frameSize = 8000  
        intervel = 0.04  
        status = STATUS_FIRST_FRAME  

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                if not buf:
                    status = STATUS_LAST_FRAME

                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())

def start_audio(time = 3,save_file="test.wav"):
    global quitmark
    start_threshold=60000
    end_threshold=40000
    endlast=10     
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = time 
    WAVE_OUTPUT_FILENAME = save_file  

    p = pyaudio.PyAudio()   
    print("录音中...")
    lcd_rect(30,40,320,90,splash_theme_color,-1)
    draw.rectangle((20,30,300,100), splash_theme_color, 'white',width=3)
    lcd_draw_string(draw,35,48, "准备录音", color=(255,0,0), scale=font3, mono_space=False)
    display.ShowImage(splash)
    
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    start_luyin = False
    break_luyin = False
    data_list =[0]*endlast
    sum_vol=0
    while not break_luyin:
        if quitmark==1:
            print('main quit')
            break
        data = stream.read(CHUNK)
        rt_data = np.frombuffer(data,dtype=np.int16)
        fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
        fft_data = np.abs(fft_temp_data)[0:fft_temp_data.size // 2 + 1]
        vol=sum(fft_data) // len(fft_data)
        data_list.pop(0)
        data_list.append(vol)
        if vol>start_threshold:
            sum_vol+=1
            if sum_vol==2:
                print('start recording')
                start_luyin=True
        if start_luyin :
            kkk= lambda x:float(x)<end_threshold
            if all([kkk(i) for i in data_list]):
                break_luyin =True
                frames=frames[:-5]
        if start_luyin:
            frames.append(data)
        print(start_threshold)
        print(vol)
    
    print('auto end')

    if quitmark==0:
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,30,300,100), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,48, "录音完毕!", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')  
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    

#define colors
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)
#display init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

#font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",16)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc",24)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)
    
def action(act):
    commandlist=['前进','后退','左转','右转','左平移','右平移','跳舞','俯卧撑','撒尿','坐下','挥手','伸懒腰','握手','祈祷','觅食','鸡头']
    mincmd=0
    minindex=len(commandlist)
    mark=False
    acts=0
    for i,cmd in enumerate(commandlist):
        ix=act.find(cmd)
        if ix>-1 and ix<=minindex:
            mincmd=i+1
            minindex=ix
            mark=True
            acts=1
    if mark:
        if mincmd==1:
            dog.move_x(12)
            time.sleep(3)
            dog.reset()
        elif mincmd==2:
            dog.move_x(-12)
            time.sleep(3)
            dog.reset()
        elif mincmd==3:
            dog.turn(60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd==4:
            dog.turn(-60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd==5:
            dog.move_y(6)
            time.sleep(3)
            dog.reset()
        elif mincmd==6:
            dog.move_y(-6)
            time.sleep(3)
            dog.reset()
        elif mincmd==7:#dacne
            dog.action(23)
            time.sleep(3)
        elif mincmd==8:#Grab
            dog.action(21)
            time.sleep(3)
        elif mincmd==9:#take a pee
            dog.action(11)
            time.sleep(3)
        elif mincmd==10:#sit down
            dog.action(12)
            time.sleep(3)
        elif mincmd==11:#wave hand
            dog.action(13)
            time.sleep(3)
        elif mincmd==12:#stretch
            dog.action(14)
            time.sleep(3)
        elif mincmd==13:
            dog.action(19)
            time.sleep(3)
        elif mincmd==14:
            dog.action(17)
            time.sleep(3)
        elif mincmd==15:
            dog.action(18)
            time.sleep(3)
        elif mincmd==16:
            dog.action(20)
            time.sleep(3)
        tttime.sleep(3)
    else:
        print('command not find')
        dog.reset()


import requests
net=False
try:
    html = requests.get("http://www.baidu.com",timeout=2)
    net=True
except:
    net=False

if net:
    dog = XGO(port='/dev/ttyAMA0',version="xgolite")
    #draw.line((2,98,318,98), fill=(255,255,255), width=2)
    draw.rectangle((20,30,300,100), splash_theme_color, 'white',width=3)
    lcd_draw_string(draw,57,100, "请说以下关键词:", color=(255,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,10,130, "前进|后退|左转|右转", color=(0,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,10,150, "左平移|右平移|跳舞", color=(0,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,10,170, "俯卧撑|撒尿|坐下|招手", color=(0,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,10,190, "伸懒腰|握手|祈祷", color=(0,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,10,210, "觅食|鸡头", color=(0,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
        
    #time.sleep(2)
    while 1:
        start_audio()
        if quitmark==0:
            xunfei=''
            time1 = datetime.now()
            wsParam = Ws_Param(APPID='7582fa81', APISecret='NzIyYzFkY2NiMzBiMTY1ZjUwYTg4MTFm',
                            APIKey='924c1939fdffc06651a49289e2fc17f4',
                            AudioFile='test.wav')
            lcd_rect(30,40,320,90,splash_theme_color,-1)
            draw.rectangle((20,30,300,100), splash_theme_color, 'white',width=3)
            lcd_draw_string(draw,35,48, "识别中...", color=(255,0,0), scale=font3, mono_space=False)
            display.ShowImage(splash)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            time2 = datetime.now()
            print(time2-time1)
            lcd_rect(30,40,320,90,splash_theme_color,-1)
            draw.rectangle((20,30,300,100), splash_theme_color, 'white',width=3)
            lcd_draw_string(draw,35,48,xunfei, color=(255,0,0), scale=font3, mono_space=False)
            display.ShowImage(splash)
            action(xunfei)
        if quitmark==1:
            print('main quit')
            break

else:
    lcd_draw_string(draw,57,70, "无法运行在没有网络的环境中!", color=(255,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,57,120, "按C键退出程序。", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    while 1:
        if button.press_b():
            break









