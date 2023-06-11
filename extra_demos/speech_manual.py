import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
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
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button

import pyaudio
import wave

from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")

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
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 8000
    RECORD_SECONDS = time  
    WAVE_OUTPUT_FILENAME = save_file   

    p = pyaudio.PyAudio()   
    print("start")
    lcd_rect(0,40,320,97,splash_theme_color,-1)
    lcd_draw_string(draw,15,45, "START RECORDING", color=(255,0,0), scale=font3, mono_space=False)
    display.ShowImage(splash)
    

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("end")
    lcd_rect(0,40,320,97,splash_theme_color,-1)
    lcd_draw_string(draw,15,45, "RECORDING DONE!", color=(255,0,0), scale=font3, mono_space=False)
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
    

btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
button=Button()
font1 = ImageFont.truetype("msyh.ttc",15)
font2 = ImageFont.truetype("msyh.ttc",22)
font3 = ImageFont.truetype("msyh.ttc",30)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
button=Button()

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)
    
def action(act):
    commandlist=['觅食','握手','转圈','爬行','摇摆','吃饭','招手','撒尿','坐下','站立','趴下','蹲起','伸懒腰','波浪']
    actionlist=[17,19,4,3,16,18,13,11,12,2,1,6,14,15]
    mincmd=0
    minindex=len(commandlist)
    mark=False
    for i,cmd in enumerate(commandlist):
        ix=act.find(cmd)
        if ix>-1 and ix<=minindex:
            mincmd=i
            minindex=ix
            mark=True
    if mark:
        print(commandlist[mincmd])
        dog.action(actionlist[mincmd])
    else:
        print('command not find')
        dog.reset()
    
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
draw.line((2,98,318,98), fill=(255,255,255), width=2)
lcd_draw_string(draw,33,10, "Mandarin to Text Demo", color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,27,100, "Please say the following:", color=(255,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,35,125, "觅食、握手、转圈、爬行", color=(0,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,35,150, "摇摆、吃饭、招手、撒尿", color=(0,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,35,175, "坐下、站立、趴下、蹲起", color=(0,255,255), scale=font2, mono_space=False)
lcd_draw_string(draw,90,200, "伸懒腰、波浪", color=(0,255,255), scale=font2, mono_space=False)
display.ShowImage(splash)
    
    
while 1:
    if button.press_c():
        lcd_rect(0,40,320,97,splash_theme_color,-1)
        lcd_draw_string(draw,15,45,'Ready for Recording', color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        start_audio()
        xunfei=''
        time1 = datetime.now()
        wsParam = Ws_Param(APPID='7582fa81', APISecret='NzIyYzFkY2NiMzBiMTY1ZjUwYTg4MTFm',
                           APIKey='924c1939fdffc06651a49289e2fc17f4',
                           AudioFile='test.wav')
        lcd_rect(0,40,320,97,splash_theme_color,-1)
        lcd_draw_string(draw,15,45, "Identifying...", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        time2 = datetime.now()
        print(time2-time1)
        lcd_rect(0,40,320,97,splash_theme_color,-1)
        lcd_draw_string(draw,15,45,xunfei, color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        action(xunfei)
    if button.press_b():
        break








