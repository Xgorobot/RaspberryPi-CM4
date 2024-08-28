from xgolib import XGO
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
import cv2

btn_selected = (24, 47, 223)
btn_unselected = (20, 30, 53)
txt_selected = (255, 255, 255)
txt_unselected = (76, 86, 127)
splash_theme_color = (15, 21, 46)
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_red = (238, 55, 59)
mic_purple = (24, 47, 223)
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


import random
import time

xunfei = ""


def draw_offline():
    draw.bitmap((115, 20), offline_logo, "red")
    warn_text = "Wifi未连接或无网络"
    draw.text((90, 140), warn_text, fill=(255, 255, 255), font=font3)
    display.ShowImage(splash)


def clear_top():
    draw.rectangle([(0, 0), (320, 111)], fill=splash_theme_color)


def clear_bottom():
    draw.rectangle([(0, 111), (320, 240)], fill=splash_theme_color)


# -------------------------------------------------------------------------------
from xgolib import XGO
import os, socket, sys, time
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
import threading
from subprocess import Popen
import requests
import base64

from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command, default_libpath
from datetime import datetime

import pyaudio
import wave
import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU

xgo = XGOEDU()

import pyaudio
import wave

import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU


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
play_anmi = True


def action(num):
    global quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_b():
            quitmark = 1


def mode(num):
    start = 120
    lcd_rect(start, 0, 300, 19, splash_theme_color, -1)
    # lcd_draw_string(
    #     draw, start, 0, "Auto Mode", color=(255, 0, 0), scale=font2, mono_space=False
    # )
    display.ShowImage(splash)
    global automark, quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_c():
            automark = not automark
            if automark:
                lcd_rect(start, 0, 300, 19, splash_theme_color, -1)
                # lcd_draw_string(draw,start,0,"Auto Mode",color=(255, 0, 0),scale=font2,mono_space=False,)
                display.ShowImage(splash)
            else:
                lcd_rect(start, 0, 300, 19, splash_theme_color, -1)
                # lcd_draw_string(draw,start,0,"Manual Mode",color=(255, 0, 0),scale=font2,mono_space=False,)
                display.ShowImage(splash)
            print(automark)


mode_button = threading.Thread(target=mode, args=(0,))
mode_button.start()

check_button = threading.Thread(target=action, args=(0,))
check_button.start()


def get_wav_duration():
    filename = "test.wav"
    with wave.open(filename, "rb") as wav_file:
        n_frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()

        duration = n_frames / frame_rate
        return duration


def gpt(speech_text):
    from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
    from sparkai.core.messages import ChatMessage

    SPARKAI_URL = "wss://spark-api.xf-yun.com/v4.0/chat"
    SPARKAI_APP_ID = "204e2232"
    SPARKAI_API_SECRET = "MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2"
    SPARKAI_API_KEY = "1896d14df5cd043b25a7bc6bee426092"
    SPARKAI_DOMAIN = "4.0Ultra"

    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    global play_anmi
    play_anmi = True
    play_wait_anmi1 = threading.Thread(target=recog_anmi, args=(0,))
    play_wait_anmi1.start()
    messages = [ChatMessage(role="user", content=speech_text)]
    handler = ChunkPrintHandler()
    a = spark.generate([messages], callbacks=[handler])
    play_anmi = False
    return a.generations[0][0].text


def start_audio(timel=3, save_file="test.wav"):
    global automark, quitmark
    start_threshold = 60000
    end_threshold = 40000
    endlast = 10
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = timel
    WAVE_OUTPUT_FILENAME = save_file

    if automark:
        p = pyaudio.PyAudio()
        stream_a = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        start_luyin = False
        break_luyin = False
        data_list = [0] * endlast
        sum_vol = 0
        audio_stream = AudiostreamSource()
        libpath = "./demos/libnyumaya_premium.so.3.1.0"
        extractor = FeatureExtractor(libpath)
        detector = AudioRecognition(libpath)
        extactor_gain = 1.0
        keywordIdlulu = detector.addModel("./demos/src/lulu_v3.1.907.premium", 0.6)
        bufsize = detector.getInputDataSize()
        audio_stream.start()

        while not break_luyin:
            if not automark:
                break_luyin = True
            if quitmark == 1:
                print("main quit")
                break
            frame = audio_stream.read(bufsize * 2, bufsize * 2)
            if not frame:
                continue
            features = extractor.signalToMel(frame, extactor_gain)
            prediction = detector.runDetection(features)
            if prediction != 0:
                now = datetime.now().strftime("%d.%b %Y %H:%M:%S")
                if prediction == keywordIdlulu:
                    print("lulu detected:" + now)
                os.system(play_command + " ./demos/src/ding.wav")
                break
            data = stream_a.read(CHUNK, exception_on_overflow=False)
            rt_data = np.frombuffer(data, dtype=np.int16)
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
            vol = sum(fft_data) // len(fft_data)
            data_list.pop(0)
            data_list.append(vol)
            print(start_threshold, vol)
            free_anmi("before")
        audio_stream.stop()
        for i in range(0, 30):
            free_anmi("after")
            time.sleep(0.03)
        while not break_luyin:
            if not automark:
                break_luyin = True
            if quitmark == 1:
                print("main quit")
                break
            data = stream_a.read(CHUNK, exception_on_overflow=False)
            rt_data = np.frombuffer(data, dtype=np.int16)
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
            vol = sum(fft_data) // len(fft_data)
            data_list.pop(0)
            data_list.append(vol)
            if vol > start_threshold:
                sum_vol += 1
                if sum_vol == 1:
                    print("start recording")
                    start_luyin = True
            if start_luyin:
                kkk = lambda x: float(x) < end_threshold
                if all([kkk(i) for i in data_list]):
                    break_luyin = True
                    frames = frames[:-5]
            if start_luyin:
                frames.append(data)
            print(start_threshold, vol)
            free_anmi("waiting")
        print("auto end")
    else:
        p = pyaudio.PyAudio()
        print("录音中...")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        stream_m = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        start_luyin = False
        break_luyin = False
        data_list = [0] * endlast
        sum_vol = 0
        while not break_luyin:
            if automark:
                break
            if quitmark == 1:
                print("main quit")
                break
            if button.press_d():
                lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
                display.ShowImage(splash)
                print("start recording")
                while 1:
                    data = stream_m.read(CHUNK, exception_on_overflow=False)
                    rt_data = np.frombuffer(data, dtype=np.int16)
                    fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
                    fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
                    vol = sum(fft_data) // len(fft_data)
                    data_list.pop(0)
                    data_list.append(vol)
                    frames.append(data)
                    print(start_threshold)
                    print(vol)
                    draw_wave(int(vol / 10000))
                    display.ShowImage(splash)
                    if button.press_d():
                        break_luyin = True
                        frames = frames[:-5]
                        break
                    if automark:
                        break
        time.sleep(0.3)
        print("manual end")

    if quitmark == 0:
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

        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()


#!/usr/bin/env python3
# -*-coding:utf-8 -*-
import ssl
import _thread as thread

import jsonpath
import websocket

from sample import ne_utils, aipass_client
import os
from data import *


# 收到websocket连接建立的处理
def on_open_tts(ws):
    def run():
        # 清除文件
        try:
            os.remove("tts.mp3")
        except:
            print("no tts.mp3")
        exist_audio = jsonpath.jsonpath(request_data, "$.payload.*.audio")
        exist_video = jsonpath.jsonpath(request_data, "$.payload.*.video")
        multi_mode = True if exist_audio and exist_video else False

        # 获取frame，用于设置发送数据的频率
        frame_rate = None
        if jsonpath.jsonpath(request_data, "$.payload.*.frame_rate"):
            frame_rate = jsonpath.jsonpath(request_data, "$.payload.*.frame_rate")[0]
        time_interval = 40
        if frame_rate:
            time_interval = round((1 / frame_rate) * 1000)

        # 获取待发送的数据
        request_data["payload"]["text"]["text"] = "spark_tts.txt"
        request_data["payload"]["user_text"]["text"] = "spark_tts.txt"
        print(request_data)
        media_path2data = aipass_client.prepare_req_data(request_data)
        # 发送数据
        aipass_client.send_ws_stream(
            ws, request_data, media_path2data, multi_mode, time_interval
        )

    thread.start_new_thread(run, ())


# 收到websocket消息的处理
def on_message_tts(ws, message):
    aipass_client.deal_message(ws, message)


# 收到websocket错误的处理
def on_error_tts(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close_tts(ws, a, b):
    print("### 执行结束，连接自动关闭 ###")


def sprak_tts(content):
    processed_s = "\n".join(
        line.strip() for line in content.splitlines() if line.strip()
    )
    with open("spark_tts.txt", "w", encoding="utf-8") as file:
        file.write(processed_s)
    global play_anmi
    play_anmi = True
    time.sleep(0.5)
    play_wait_anmi = threading.Thread(target=recog_anmi, args=(0,))
    play_wait_anmi.start()
    request_data["header"]["app_id"] = APPId
    auth_request_url = ne_utils.build_auth_request_url(
        request_url, "GET", APIKey, APISecret
    )
    websocket.enableTrace(False)
    ws_tts = websocket.WebSocketApp(
        auth_request_url,
        on_message=on_message_tts,
        on_error=on_error_tts,
        on_close=on_close_tts,
    )
    ws_tts.on_open = on_open_tts
    ws_tts.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    play_anmi = False
    time.sleep(0.5)
    proc = Popen("mplayer tts.mp3", shell=True)
    play_anmi = True
    play_wait_anmi = threading.Thread(target=speak_anmi, args=(0,))
    play_wait_anmi.start()
    proc.wait()
    time.sleep(0.5)
    play_anmi = False


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
        self.BusinessArgs = {
            "domain": "iat",
            "language": "zh_cn",
            "accent": "mandarin",
            "vinfo": 1,
            "vad_eos": 10000,
        }

    # 生成url
    def create_url(self):
        url = "wss://ws-api.xfyun.cn/v2/iat"
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = (
            'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
            % (self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )
        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        # 拼接鉴权参数，生成url
        url = url + "?" + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理
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
            result = json.dumps(data, ensure_ascii=False)
            tx = ""
            for r in data:
                tx += r["cw"][0]["w"]
            xunfei += tx

            # textshow=sid.split(" ")[1]

    except Exception as e:
        print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, a, b):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = (
            STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        )

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

                    d = {
                        "common": wsParam.CommonArgs,
                        "business": wsParam.BusinessArgs,
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        },
                    }
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {
                        "data": {
                            "status": 1,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        }
                    }
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        }
                    }
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


def free_anmi(kinds):
    global ani_num
    if kinds == "after":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "after"
        pic_num = 30
    elif kinds == "before":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "before"
        pic_num = 42
    elif kinds == "recog":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "recog"
        pic_num = 90
    elif kinds == "speak1":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak1/"
        pic_num = 74
    elif kinds == "speak2":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak2/"
        pic_num = 53
    elif kinds == "speak3":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak3/"
        pic_num = 86
    elif kinds == "speak4":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak4/"
        pic_num = 87
    elif kinds == "waiting":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "waiting"
        pic_num = 114

    ani_num += 1
    if ani_num >= pic_num:
        ani_num = 0
    exp = Image.open(pic_path + expression_name_cs + str(ani_num + 1) + ".png")
    display.ShowImage(exp)


def recog_anmi(t):
    global play_anmi
    print("recog_anmi", play_anmi)
    while 1:
        free_anmi("recog")
        time.sleep(0.02)
        if play_anmi == False:
            break


def speak_anmi(t):
    global play_anmi
    rn = random.randint(1, 4)
    while 1:
        if rn == 1:
            free_anmi("speak1")
        elif rn == 2:
            free_anmi("speak2")
        elif rn == 3:
            free_anmi("speak2")
        elif rn == 4:
            free_anmi("speak2")
        time.sleep(0.02)
        if play_anmi == False:
            break


ani_num = 0
import requests
from subprocess import Popen

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    proc = Popen("sudo cpufreq-set -f 1.5GHz", shell=True)
    play_anmi = True
    while 1:
        clear_bottom()
        clear_top()
        start_audio()
        if quitmark == 0:
            xunfei = ""
            # SpeechRecognition
            wsParam = Ws_Param(
                APPID="7582fa81",
                APISecret="NzIyYzFkY2NiMzBiMTY1ZjUwYTg4MTFm",
                APIKey="924c1939fdffc06651a49289e2fc17f4",
                AudioFile="test.wav",
            )
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(
                wsUrl, on_message=on_message, on_error=on_error, on_close=on_close
            )
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            speech_text = xunfei
            if speech_text != "":
                print(speech_text)
                re = gpt(speech_text)
                print(re)
                sprak_tts(re)

        if quitmark == 1:
            print("main quit")
            break

else:
    draw_offline()
    while 1:
        if button.press_b():
            break

proc = Popen("sudo cpufreq-set -g conservative", shell=True)
