# 星火文成图 demo
import time

import requests
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
from PIL import Image
from io import BytesIO

class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


# 生成鉴权url
def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)

# 生成请求body体
def getBody(appid,text):
    body= {
        "header": {
            "app_id": appid,
            "uid":"123456789"
        },
        "parameter": {
            "chat": {
                "domain": "general",
                "temperature":0.5,
                "max_tokens":4096
            }
        },
        "payload": {
            "message":{
                "text":[
                    {
                        "role":"user",
                        "content":text
                    }
                ]
            }
        }
    }
    return body

# 发起请求并返回结果
def main(text,appid,apikey,apisecret):
    host = 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti'
    url = assemble_ws_auth_url(host,method='POST',api_key=apikey,api_secret=apisecret)
    content = getBody(appid,text)
    print(time.time())
    response = requests.post(url,json=content,headers={'content-type': "application/json"}).text
    print(time.time())
    return response

#将base64 的图片数据存在本地
def base64_to_image(base64_data, save_path):
    # 解码base64数据
    img_data = base64.b64decode(base64_data)

    # 将解码后的数据转换为图片
    img = Image.open(BytesIO(img_data))

    # 保存图片到本地
    img.save(save_path)


# 解析并保存到指定位置
def parser_Message(message):
    data = json.loads(message)
    # print("data" + str(message))
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
    else:
        text = data["payload"]["choices"]["text"]
        imageContent = text[0]
        # if('image' == imageContent["content_type"]):
        imageBase = imageContent["content"]
        imageName = data['header']['sid']
        savePath = f"original.jpg"
        base64_to_image(imageBase,savePath)
        print("图片保存路径：" + savePath)

#星火语音识别demo
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理
def on_message(ws, message):
    global xunfei
    print('on message')
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
            print(xunfei)

            #textshow=sid.split(" ")[1]


    except Exception as e:
        print("receive msg,but parse exception:", e)



# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,a,b):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


import requests
from PIL import Image

import os, math
from xgolib import XGO
import cv2
import os, socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
import threading
import json, base64

from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command, default_libpath
from datetime import datetime


import pyaudio
import wave

import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU

xgo = XGOEDU()

btn_selected = (24, 47, 223)
btn_unselected = (20, 30, 53)
txt_selected = (255, 255, 255)
txt_unselected = (76, 86, 127)
splash_theme_color = (15, 21, 46)
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_red = (238, 55, 59)
# display init
display = LCD_2inch.LCD_2inch()
# display.Init()
display.clear()

# font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc", 15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 16)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc", 18)
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)


def lcd_draw_string(
    splash,
    x,
    y,
    text,
    color=(255, 255, 255),
    font_size=1,
    scale=1,
    mono_space=False,
    auto_wrap=True,
    background_color=(0, 0, 0),
):
    splash.text((x, y), text, fill=color, font=scale)


def lcd_rect(x, y, w, h, color, thickness):
    draw.rectangle([(x, y), (w, h)], fill=color, width=thickness)


quitmark = 0
automark = True
button = Button()


def action(num):
    global quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_b():
            quitmark = 1


check_button = threading.Thread(target=action, args=(0,))
check_button.start()


def split_string(text):
    import re

    seg = 30
    result = []
    current_segment = ""
    current_length = 0

    for char in text:
        is_chinese = bool(re.match(r"[\u4e00-\u9fa5]", char))

        if is_chinese:
            char_length = 2
        else:
            char_length = 1

        if current_length + char_length <= seg:
            current_segment += char
            current_length += char_length
        else:
            result.append(current_segment)
            current_segment = char
            current_length = char_length

    if current_segment:
        result.append(current_segment)

    return result


def scroll_text_on_lcd(text, x, y, max_lines, delay):
    lines = text.split("\n")
    total_lines = len(lines)
    for i in range(total_lines - max_lines):
        lcd_rect(0, 90, 320, 290, splash_theme_color, -1)
        visible_lines = lines[i : i + max_lines - 1]
        last_line = lines[i + max_lines - 1]

        for j in range(max_lines - 1):
            lcd_draw_string(
                draw,
                x,
                y + j * 20,
                visible_lines[j],
                color=(255, 255, 255),
                scale=font2,
                mono_space=False,
            )
        lcd_draw_string(
            draw,
            x,
            y + (max_lines - 1) * 20,
            last_line,
            color=(255, 255, 255),
            scale=font2,
            mono_space=False,
        )

        display.ShowImage(splash)
        time.sleep(delay)


def start_audio(timel = 3,save_file="test.wav"):
    global automark,quitmark
    start_threshold=60000
    end_threshold=40000
    endlast=10     
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = timel
    WAVE_OUTPUT_FILENAME = save_file  

    
    if automark:
        p = pyaudio.PyAudio()   
        print("正在聆听")
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,40, "正在聆听", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        
        
        stream_a = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        frames = []
        start_luyin = False
        break_luyin = False
        data_list =[0]*endlast
        sum_vol=0
        audio_stream = AudiostreamSource()

        libpath='./demos/libnyumaya_premium.so.3.1.0'
        extractor = FeatureExtractor(libpath)
        detector = AudioRecognition(libpath)

        extactor_gain = 1.0

        #Add one or more keyword models
        keywordIdlulu = detector.addModel('./demos/src/lulu_v3.1.907.premium',0.6)

        bufsize = detector.getInputDataSize()

        audio_stream.start()
        while not break_luyin:
            if not automark:
                break_luyin=True
            if quitmark==1:
                print('main quit')
                break
            frame = audio_stream.read(bufsize*2,bufsize*2)
            if(not frame):
                time.sleep(0.01)
                continue

            features = extractor.signalToMel(frame,extactor_gain)
            prediction = detector.runDetection(features)
            if(prediction != 0):
                now = datetime.now().strftime("%d.%b %Y %H:%M:%S")
                if(prediction == keywordIdlulu):
                    print("lulu detected:" + now)
                os.system(play_command + " ./demos/src/ding.wav")
                break
        audio_stream.stop()
        while not break_luyin:
            if not automark:
                break_luyin=True
            if quitmark==1:
                print('main quit')
                break
            data = stream_a.read(CHUNK,exception_on_overflow=False)
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
    else:
        p = pyaudio.PyAudio()   
        print("录音中...")
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,40, "按B键开始", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        
        
        stream_m = p.open(format=FORMAT,
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
            if automark:
                break
            if quitmark==1:
                print('main quit')
                break
            if button.press_d():
                lcd_rect(30,40,320,90,splash_theme_color,-1)
                draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
                lcd_draw_string(draw,35,40, "正在聆听，按B健停止", color=(255,0,0), scale=font3, mono_space=False)
                display.ShowImage(splash)
                print('start recording')
                while 1:
                    data = stream_m.read(CHUNK,exception_on_overflow=False)
                    rt_data = np.frombuffer(data,dtype=np.int16)
                    fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
                    fft_data = np.abs(fft_temp_data)[0:fft_temp_data.size // 2 + 1]
                    vol=sum(fft_data) // len(fft_data)
                    data_list.pop(0)
                    data_list.append(vol)
                    frames.append(data)
                    print(start_threshold)
                    print(vol)
                    if button.press_d():
                        break_luyin =True
                        frames=frames[:-5]
                        break
                    if automark:
                        break
                
            
        time.sleep(0.3)
        print('manual end')

    if quitmark==0:
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,40, "录音完毕!", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)
        try:
            stream_a.stop_stream()
            stream_a.close()
        except:
            pass
        try:
            stream_m.stop_stream()
            stream_m.close()
        except:
            pass
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')  
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

def resize_image(image_path, output_path, size=(320, 240)):
    with Image.open(image_path) as img:
        img_resized = img.resize(size)
        img_resized.save(output_path)
        print(f"Image resized successfully and saved at {output_path}")


def gpt_draw(scr):
    global quitmark
    APPID ='204e2232'
    APISecret = 'MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2'
    APIKEY = '1896d14df5cd043b25a7bc6bee426092'
    desc = scr
    res = main(desc,appid=APPID,apikey=APIKEY,apisecret=APISecret)
    parser_Message(res)
    original_image_path = "original.jpg"
    resized_image_path = "resized.jpg"
    resize_image(original_image_path, resized_image_path)
    if quitmark == 1:
        print("main quit")
        return 0
    image = Image.open("resized.jpg")
    splash.paste(image, (0, 0))
    display.ShowImage(splash)
    if quitmark == 1:
        print("main quit")
        return 0
    time.sleep(6)


import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

xunfei = ""
if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
    display.ShowImage(splash)

    while 1:
        start_audio()
        if quitmark == 0:
            xunfei=''
            wsParam = Ws_Param(APPID='7582fa81', APISecret='NzIyYzFkY2NiMzBiMTY1ZjUwYTg4MTFm',
                            APIKey='924c1939fdffc06651a49289e2fc17f4',
                            AudioFile='test.wav')
            lcd_rect(30,40,320,90,splash_theme_color,-1)
            draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
            lcd_draw_string(draw,35,40, "正在识别", color=(255,0,0), scale=font3, mono_space=False)
            display.ShowImage(splash)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            speech_text=xunfei
            print('rec result-----------------------------------')
            print(xunfei)
            if speech_text != "":
                speech_list = split_string(speech_text)
                print(speech_list)
                for sp in speech_list:
                    lcd_rect(0, 40, 320, 290, splash_theme_color, -1)
                    draw.rectangle(
                        (20, 30, 300, 80), splash_theme_color, "white", width=3
                    )
                    lcd_draw_string(
                        draw,
                        35,
                        40,
                        sp,
                        color=(255, 0, 0),
                        scale=font3,
                        mono_space=False,
                    )
                    lcd_draw_string(
                        draw,
                        27,
                        90,
                        "正在等待星火大模型",
                        color=(255, 255, 255),
                        scale=font2,
                        mono_space=False,
                    )
                    display.ShowImage(splash)
                    time.sleep(1.5)
                re = gpt_draw(speech_text)
                splash = Image.new(
                    "RGB", (display.height, display.width), splash_theme_color
                )
                draw = ImageDraw.Draw(splash)
                display.ShowImage(splash)

        if quitmark == 1:
            print("main quit")
            break

else:
    lcd_draw_string(
        draw,
        57,
        70,
        "无法在没有网络的环境中运行!",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        57,
        120,
        "按C键退出。",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)
    while 1:
        if button.press_b():
            break
