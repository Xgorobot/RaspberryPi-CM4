import os, re
from xgolib import XGO
import cv2
import os, socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
import threading
import json, base64
import subprocess

import pyaudio
import wave

import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU

from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command, default_libpath
from datetime import datetime

xgo = XGOEDU()

prompt = """
【角色】请扮演一个资深的机器人开发者，你精通树莓派，机器人和python开发。
【任务】根据命令词让机器狗按照提供的python库自动生成python代码。
【要求】根据命令词语自动生成的python代码，必须输出md格式的文档。
具体的python库如下，机器狗的身体控制接口,分别为前进，后退、左平移、右平移，旋转、沿XYZ轴三个轴方向平移和旋转，动作组，机械臂，单腿控制和单舵机控制等。
机器狗的头部控制接口,分别屏幕，按键，多媒体，视觉和语音功能等
机器狗身体的控制接口函数在下文有详细的描述和示例。
xgo.move_x(step)  #step的单位为毫米,前进为正,后退为负，0表示停止，取值范围是[-25,25]mm。
xgo.move_y(step)  #step的单位为毫米,左平移为正,右平移为负，0表示停止，取值范围是[-18,18]mm。
xgo.turn(speed)  #speed为角速度, 正数为顺时针,负数为逆时针，0表示停止，取值范围是[-150,150] 。
xgo.pace(mode) #mode为slow,normal或者high 。表示机器狗的运动速度，slow表示慢速，normal表示速度，high表示高速。
time.sleep(x) #X的单位是秒，表示上一条指令运动时长。
xgo.action(id) #id为动作组接口，id取值范围为1-24,分别对应[趴下,站起,转圈,匍匐前进,原地踏步,蹲起,沿x转动,沿y转动,沿z转动,三轴转动,撒尿,坐下,招手,伸懒腰,波浪运动,摇摆运动,求食,找食物,握手,展示机械臂,俯卧撑，张望，跳舞，调皮]，其中机械臂的上抓，中抓，下抓对应的id分别为128，129，130。举例说明，即趴下的id为1,匍匐前进为4,求食为18
xgo.translation(direction, data)  # direction取值为'x','y','z' ,data的单位是毫米，沿X轴正方向平移为正数，0表示回到初始位置，沿着X负方向平移为负数，取值范围是[-35,35]mm，y轴和z轴同理。
xgo.attitude(direction, data)  #direction取值为'r','p','y' ,data的单位是度，沿X轴正时针旋转为正数，0表示回到初始位置，沿着X逆时针旋转为负数，取值范围是[-20,20]mm，y轴和z轴旋转运动同理。
arm( arm_x, arm_z) #表示arm_x取值范围是[-80,155]和arm_z的取值范围是[-95，155]。
motor(motor_id, data)#motor_id的取值范围是 [11,12,13,21,22,23,31,32,33,41,42,43,51,52,53]，data表示舵机角度。
claw(pos) #pos的取值是0-255，其中0表示夹爪完全张开，255表示夹爪完全闭合。
imu(mode) #mode的取值为0或者1，0代表关闭自稳定模式，1表示打开自稳定模式。
perform(mode)#mode的取值为0或者1，0代表关闭表演模式，1表示打开表演模式。
read_battery()#读取当前电池电量， 读取成功则返回1-100的整数，代表电池剩余电量百分比， 读取失败则返回0。
reset()# 这个函数是让机器狗复位。
机器狗头部的控制接口函数在下文有详细的描述和示例。
lcd_picture(filename)   #此函数用于机器狗显示表情，有攻击，愤怒，厌恶，喜欢，调皮，祈祷，伤心，敏感，困，道歉，惊讶, filename对应的参数是attack, anger, disgust, like, naughty, pray, sad, sensitive, sleepy, apologize, surprise.
xgoSpeaker(filename) #此函数用于机器狗发出声音，有攻击，愤怒，厌恶，喜欢，调皮，祈祷，伤心，敏感，困，道歉，惊讶, filename对应的参数是attack, anger, disgust, like, naughty, pray, sad, sensitive, sleepy, apologize, surprise.
我希望你能根据我的命令,利用以上函数写出对应的控制代码。

下面我会给你一些例子形式为(命令,代码):

请在每个程序前加上以下两句初始化代码
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO("xgolite")
XGO_edu = XGOEDU()

示例1
命令:前进5秒
代码:
import time
from xgolib import XGO
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)


示例2
命令:左平移5秒
代码:
import time
from xgolib import XGO
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
xgo.move_y(15)
time.sleep(5)
xgo.move_y(0)


示例3
命令:以100的角速度旋转3秒
代码:
import time
from xgolib import XGO
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
xgo.turn(100)
time.sleep(3)
xgo.turn(0)



示例4
命令:前进3秒,撒个尿,左转3秒,展示机械臂:
import time
from xgolib import XGO
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)
xgo.action(11)
xgo.turn(100)
time.sleep(3)
xgo.turn(0)
xgo.action(20)


示例5
命令：显示开心的表情并发出开心的声音，并伸懒腰
import time
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
XGO_edu = XGOEDU()
xgo.action(14)
time.sleep(3)
XGO_edu.lcd_picture(like) 
XGO_edu.xgoSpeaker(like)
示例结束了，请根据命令返回python代码，把注释写在返回的代码里面，最后一句是xgo.reset()让其复位，用到随机的画不要忘了加入import random，你必须输出md格式的文档。
"""

# 20240523 AI升级至星火3.5max 版本
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

SPARKAI_URL = "wss://spark-api.xf-yun.com/v3.5/chat"
SPARKAI_APP_ID = "204e2232"
SPARKAI_API_SECRET = "MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2"
SPARKAI_API_KEY = "1896d14df5cd043b25a7bc6bee426092"
SPARKAI_DOMAIN = "generalv3.5"


spark = ChatSparkLLM(
    spark_api_url=SPARKAI_URL,
    spark_app_id=SPARKAI_APP_ID,
    spark_api_key=SPARKAI_API_KEY,
    spark_api_secret=SPARKAI_API_SECRET,
    spark_llm_domain=SPARKAI_DOMAIN,
    streaming=False,
)

xunfei = ""
text = []


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
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 17)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc", 20)
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
            os._exit(0)


def mode(num):
    start = 130
    lcd_rect(start, 0, 200, 19, splash_theme_color, -1)
    lcd_draw_string(
        draw, start, 0, "自动模式", color=(255, 0, 0), scale=font2, mono_space=False
    )
    display.ShowImage(splash)
    global automark, quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_c():
            automark = not automark
            if automark:
                lcd_rect(start, 0, 200, 19, splash_theme_color, -1)
                lcd_draw_string(
                    draw,
                    start,
                    0,
                    "自动模式",
                    color=(255, 0, 0),
                    scale=font2,
                    mono_space=False,
                )
                display.ShowImage(splash)
            else:
                lcd_rect(start, 0, 200, 19, splash_theme_color, -1)
                lcd_draw_string(
                    draw,
                    start,
                    0,
                    "手动模式",
                    color=(255, 0, 0),
                    scale=font2,
                    mono_space=False,
                )
                display.ShowImage(splash)
            print(automark)


mode_button = threading.Thread(target=mode, args=(0,))
mode_button.start()

check_button = threading.Thread(target=action, args=(0,))
check_button.start()


def gpt(speech_text):
    messages = [
        ChatMessage(role="system", content=prompt),
        ChatMessage(role="user", content=speech_text),
    ]
    handler = ChunkPrintHandler()
    a = spark.generate([messages], callbacks=[handler])
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
        print("正在聆听")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw, 35, 40, "正在聆听", color=(255, 0, 0), scale=font3, mono_space=False
        )
        display.ShowImage(splash)

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

        # Add one or more keyword models
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
                time.sleep(0.01)
                continue

            features = extractor.signalToMel(frame, extactor_gain)
            prediction = detector.runDetection(features)
            if prediction != 0:
                now = datetime.now().strftime("%d.%b %Y %H:%M:%S")
                if prediction == keywordIdlulu:
                    print("lulu detected:" + now)
                os.system(play_command + " ./demos/src/ding.wav")
                break
        audio_stream.stop()
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
            print(start_threshold)
            print(vol)

        print("auto end")
    else:
        p = pyaudio.PyAudio()
        print("录音中...")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw, 35, 40, "按B键开始", color=(255, 0, 0), scale=font3, mono_space=False
        )
        display.ShowImage(splash)

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
                draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
                lcd_draw_string(
                    draw,
                    35,
                    40,
                    "正在聆听，按B健停止",
                    color=(255, 0, 0),
                    scale=font3,
                    mono_space=False,
                )
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
                    if button.press_d():
                        break_luyin = True
                        frames = frames[:-5]
                        break
                    if automark:
                        break

        time.sleep(0.3)
        print("manual end")

    if quitmark == 0:
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw, 35, 40, "录音完毕!", color=(255, 0, 0), scale=font3, mono_space=False
        )
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

        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()


def line_break(line):
    LINE_CHAR_COUNT = 19 * 2  # 每行字符数：30个中文字符(=60英文字符)
    CHAR_SIZE = 20
    TABLE_WIDTH = 4
    ret = ""
    width = 0
    for c in line:
        if len(c.encode("utf8")) == 3:  # 中文
            if LINE_CHAR_COUNT == width + 1:  # 剩余位置不够一个汉字
                width = 2
                ret += "\n" + c
            else:  # 中文宽度加2，注意换行边界
                width += 2
                ret += c
        else:
            if c == "\t":
                space_c = TABLE_WIDTH - width % TABLE_WIDTH  # 已有长度对TABLE_WIDTH取余
                ret += " " * space_c
                width += space_c
            elif c == "\n":
                width = 0
                ret += c
            else:
                width += 1
                ret += c
        if width >= LINE_CHAR_COUNT:
            ret += "\n"
            width = 0
    if ret.endswith("\n"):
        return ret
    return ret + "\n"


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


def split_string(text):
    import re

    seg = 28
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


import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    print("net")
    net = True
except:
    pass

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    # draw.line((2,98,318,98), fill=(255,255,255), width=2)
    draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
    display.ShowImage(splash)

    # time.sleep(2)
    while 1:
        start_audio()
        if quitmark == 0:
            xunfei = ""
            wsParam = Ws_Param(
                APPID="204e2232",
                APISecret="MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2",
                APIKey="1896d14df5cd043b25a7bc6bee426092",
                AudioFile="test.wav",
            )
            lcd_rect(0, 0, 320, 290, splash_theme_color, -1)
            draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
            lcd_draw_string(
                draw,
                35,
                40,
                "识别中...",
                color=(255, 0, 0),
                scale=font3,
                mono_space=False,
            )
            display.ShowImage(splash)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            ws = websocket.WebSocketApp(
                wsUrl, on_message=on_message, on_error=on_error, on_close=on_close
            )
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            speech_text = xunfei
            if speech_text != "":
                speech_list = split_string(speech_text)
                print(speech_list)
                for sp in speech_list:
                    lcd_rect(0, 0, 320, 290, splash_theme_color, -1)
                    draw.rectangle(
                        (20, 30, 300, 80), splash_theme_color, "white", width=3
                    )
                    lcd_draw_string(
                        draw,
                        35,
                        40,
                        sp,
                        color=(255, 0, 0),
                        scale=font2,
                        mono_space=False,
                    )
                    lcd_draw_string(
                        draw,
                        27,
                        90,
                        "等待AI回复...",
                        color=(255, 255, 255),
                        scale=font2,
                        mono_space=False,
                    )
                    display.ShowImage(splash)
                    time.sleep(1.5)
                res = gpt(speech_text)
                re_e = line_break(res)
                print(re_e)
                if re_e != "":
                    lcd_rect(0, 0, 320, 290, splash_theme_color, -1)
                    draw.rectangle(
                        (20, 30, 300, 80), splash_theme_color, "white", width=3
                    )
                    lcd_draw_string(
                        draw,
                        35,
                        40,
                        "代码生成中...",
                        color=(255, 0, 0),
                        scale=font3,
                        mono_space=False,
                    )
                    lcd_draw_string(
                        draw,
                        10,
                        90,
                        re_e,
                        color=(255, 255, 255),
                        scale=font2,
                        mono_space=False,
                    )
                    display.ShowImage(splash)
                    with open("cmd.py", "w") as file:
                        code_blocks = re.findall(r"```python(.*?)```", res, re.DOTALL)
                        extracted_code = []
                        for block in code_blocks:
                            code_lines = block.strip().split("\n")
                            extracted_code.append(
                                "\n".join(code_lines)
                            )  # Include all lines, including the first one
                        try:
                            file.write(extracted_code[0])
                        except:
                            file.write(res)
                    scroll_text_on_lcd(re_e, 10, 90, 7, 0.3)
                    lcd_rect(0, 0, 320, 290, splash_theme_color, -1)
                    draw.rectangle(
                        (20, 30, 300, 80), splash_theme_color, "white", width=3
                    )
                    lcd_draw_string(
                        draw,
                        35,
                        40,
                        "代码运行中...",
                        color=(255, 0, 0),
                        scale=font3,
                        mono_space=False,
                    )
                    lcd_draw_string(
                        draw,
                        10,
                        90,
                        re_e,
                        color=(255, 255, 255),
                        scale=font2,
                        mono_space=False,
                    )
                    display.ShowImage(splash)
                    try:
                        process = subprocess.Popen(["python3", "cmd.py"])
                        exitCode = process.wait()
                    except:
                        lcd_rect(0, 0, 320, 290, splash_theme_color, -1)
                        draw.rectangle(
                            (20, 30, 300, 80), splash_theme_color, "white", width=3
                        )
                        lcd_draw_string(
                            draw,
                            10,
                            90,
                            "无法正常代码。",
                            color=(255, 255, 255),
                            scale=font2,
                            mono_space=False,
                        )
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
