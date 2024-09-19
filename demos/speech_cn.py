from gpt_utils_cn import *

quitmark = 0


def action(num):
    global quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_b():
            print("quit!!!!!!!!!!!!!!!!!!!!!!!!!")
            quitmark = 1
            os._exit(0)


check_button = threading.Thread(target=action, args=(0,))
check_button.start()

xunfei = ""
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
        global quitmark
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
                if quitmark:
                    break
        ws.close()

    thread.start_new_thread(run, ())


import os


def check_type():
    os.system("sudo chmod 777 -R /dev/ttyAMA0")
    dog = XGO(port="/dev/ttyAMA0", version="xgorider")
    fm = dog.read_firmware()
    print(fm)
    if fm[0] == "M":
        print("XGO-MINI")
        dog = XGO(port="/dev/ttyAMA0", version="xgomini")
        dog_type = "M"
    elif fm[0] == "L":
        print("XGO-LITE")
        dog_type = "L"
    elif fm[0] == "R":
        print("XGO-RIDER")
        dog_type = "R"
    dog.reset()
    return dog_type


def actions_dog(act):
    commandlist = [
        "前进",
        "后退",
        "左转",
        "右转",
        "左平移",
        "右平移",
        "跳舞",
        "俯卧撑",
        "撒尿",
        "坐下",
        "挥手",
        "伸懒腰",
        "握手",
        "祈祷",
        "找食物",
        "鸡头",
        "趴下",
        "匍匐前进",
        "转圈",
        "摇摆",
        "张望",
        "调皮",
        "向上抓取",
        "中间抓取",
        "向下抓取",
        "波浪",
        "乞讨",
    ]
    mincmd = 0
    minindex = len(commandlist)
    mark = False
    acts = 0
    for i, cmd in enumerate(commandlist):
        ix = act.find(cmd)
        if ix > -1 and ix <= minindex:
            mincmd = i + 1
            minindex = ix
            mark = True
            acts = 1
    if mark:
        if mincmd == 1:
            dog.move_x(12)
            time.sleep(3)
            dog.reset()
        elif mincmd == 2:
            dog.move_x(-12)
            time.sleep(3)
            dog.reset()
        elif mincmd == 3:
            dog.turn(60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd == 4:
            dog.turn(-60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd == 5:
            dog.move_y(6)
            time.sleep(3)
            dog.reset()
        elif mincmd == 6:
            dog.move_y(-6)
            time.sleep(3)
            dog.reset()
        elif mincmd == 7:  # dacne
            dog.action(23)
            time.sleep(3)
        elif mincmd == 8:  # Grab
            dog.action(21)
            time.sleep(3)
        elif mincmd == 9:  # take a pee
            dog.action(11)
            time.sleep(3)
        elif mincmd == 10:  # sit down
            dog.action(12)
            time.sleep(3)
        elif mincmd == 11:  # wave hand
            dog.action(13)
            time.sleep(3)
        elif mincmd == 12:  # stretch
            dog.action(14)
            time.sleep(3)
        elif mincmd == 13:
            dog.action(19)
            time.sleep(3)
        elif mincmd == 14:
            dog.action(17)
            time.sleep(3)
        elif mincmd == 15:
            dog.action(18)
            time.sleep(3)
        elif mincmd == 16:
            dog.action(20)
            time.sleep(3)
        elif mincmd == 17:
            dog.action(1)
            time.sleep(3)
        elif mincmd == 18:
            dog.action(3)
            time.sleep(3)
        elif mincmd == 19:
            dog.action(4)
            time.sleep(3)
        elif mincmd == 20:
            dog.action(16)
            time.sleep(3)
        elif mincmd == 21:
            dog.action(22)
            time.sleep(3)
        elif mincmd == 22:
            dog.action(24)
            time.sleep(3)
        elif mincmd == 23:
            dog.action(128)
            time.sleep(3)
        elif mincmd == 24:
            dog.action(129)
            time.sleep(3)
        elif mincmd == 25:
            dog.action(130)
            time.sleep(3)
        elif mincmd == 26:
            dog.action(15)
            time.sleep(3)
        elif mincmd == 27:
            dog.action(17)
            time.sleep(3)

        time.sleep(3)
    else:
        time.sleep(1)
        print("command not find")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw, 35, 48, "错误命令词", color=(255, 0, 0), scale=font3, mono_space=False
        )
        display.ShowImage(splash)
        dog.reset()
        time.sleep(0.5)


def show_words_rider():
    clear_bottom()
    lcd_draw_string(
        draw,
        10,
        110,
        "前进|后退|顺时针旋转|逆时针旋转",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        130,
        "左右摇摆|高低起伏|四方蛇形|升降旋转",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)


def actions_rider(act):
    commandlist = [
        "前进",
        "后退",
        "顺时针旋转",
        "逆时针旋转",
        "左右摇摆",
        "高低起伏",
        "四方蛇形",
        "升降旋转",
    ]
    mincmd = 0
    minindex = len(commandlist)
    mark = False
    acts = 0
    for i, cmd in enumerate(commandlist):
        ix = act.find(cmd)
        if ix > -1 and ix <= minindex:
            mincmd = i + 1
            minindex = ix
            mark = True
            acts = 1
    if mark:
        if mincmd == 1:
            dog.rider_move_x(1, 1)
            time.sleep(1)
        elif mincmd == 2:
            dog.rider_move_x(-1, 1)
            time.sleep(1)
        elif mincmd == 3:
            dog.rider_turn(180, 1)
            time.sleep(1)
        elif mincmd == 4:
            dog.rider_turn(-180, 1)
            time.sleep(1)
        elif mincmd == 5:
            dog.rider_action(1, True)
            time.sleep(1)
        elif mincmd == 6:
            dog.rider_action(3, True)
            time.sleep(1)
        elif mincmd == 7:
            dog.rider_action(4, True)
            time.sleep(1)
        elif mincmd == 8:
            dog.rider_action(5, True)
            print("生姜旋转")
            time.sleep(1)
        time.sleep(3)
    else:
        time.sleep(1)
        print("command not find")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        lcd_draw_string(
            draw,
            35,
            48,
            "错误命令词",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
        )
        display.ShowImage(splash)
        dog.reset()
        time.sleep(0.5)


def show_words_dog():
    clear_bottom()
    lcd_draw_string(
        draw,
        10,
        130,
        "前进|后退|左转|右转|趴下|匍匐前进|左平移|右平移|跳舞",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        150,
        "俯卧撑|撒尿|坐下|招手|张望|调皮|伸懒腰|握手|祈祷|波浪",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        170,
        "找食物|鸡头|向上抓取|中间抓取|向下抓取|转圈|摇摆|乞讨",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)


import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    dog_type = check_type()
    print("----------------------------------------")
    print(dog_type)
    while 1:
        if dog_type == "M" or dog_type == "L":
            show_words_dog()
        elif dog_type == "R":
            show_words_rider()
        start_audio()
        if quitmark == 0:
            xunfei = ""
            # SpeechRecognition
            wsParam = Ws_Param(
                APPID="204e2232",
                APISecret="MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2",
                APIKey="1896d14df5cd043b25a7bc6bee426092",
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
            clear_bottom()
            if quitmark == 1:
                print("main quit")
                break
            if speech_text != "":
                speech_list = line_break(speech_text)
                print(speech_list)
                lcd_draw_string(
                    draw,
                    10,
                    111,
                    speech_list,
                    color=(255, 255, 255),
                    scale=font2,
                    mono_space=False,
                )
                display.ShowImage(splash)
                lines = len(speech_list.split("\n"))
                tick = 0.3
                if lines > 6:
                    scroll_text_on_lcd(re_e, 10, 111, 6, tick)
                if quitmark == 1:
                    print("main quit")
                    break
                if dog_type == "M" or dog_type == "L":
                    actions_dog(xunfei)
                elif dog_type == "R":
                    actions_rider(xunfei)
        if quitmark == 1:
            print("main quit")
            break

else:
    draw_offline()
    while 1:
        if button.press_b():
            break
