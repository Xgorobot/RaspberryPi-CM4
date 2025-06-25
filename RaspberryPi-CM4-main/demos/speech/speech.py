import os,time,threading,pyaudio,requests
import xgoscreen.LCD_2inch as LCD_2inch
from xgolib import XGO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from key import Button,language
from audio_speech import start_recording 
from language_recognize import test_one 
from doubao_speech import model_output
import logging

#version=2.0

la=language()
SPLASH_COLOR = (15, 21, 46)
FONT_PATH = "/home/jinliang/model/msyh.ttc"
FONT_SIZE = 20
DOG_PORT = '/dev/ttyAMA0'
DOG_VERSION = "xgomini"
TEST_NETWORK_URL = "http://www.baidu.com"

ACTION_MAP = {
    "Dance": (23, 6),
    "Pushups": (21, 8),
    "Pee": (11, 7),
    "Stretch": (14, 10),
    "Pray": (19, 3),
    "Chickenhead": (20, 9),
    "Lookforfood": (17, 4),
    "Grabdownwards": (130, 10),
    "Wave": (15, 6),
    "Beg": (17, 3)
}

WIFI_OFFLINE_PATH = "/home/jinliang/RaspberryPi-CM4-main/pics/offline.png"
font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 22)
color_white = (255, 255, 255)
mic_purple = (24, 47, 223)

import pyaudio
from auto_platform import AudiostreamSource
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
class DogController:
    def __init__(self):
        self.display = LCD_2inch.LCD_2inch()
        self.display.Init()
        
        self.splash = Image.new("RGB", (self.display.height, self.display.width), SPLASH_COLOR)
        self.draw = ImageDraw.Draw(self.splash)
        self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        
        self.dog = XGO(port=DOG_PORT, version=DOG_VERSION)
        self.button = Button()
        self.audio_stream = None
        self.stream_a = None
        self.p = None
        self.network_available = False
        
        # 启动按键检测线程
        self._start_button_thread()
        try:
            wifi_img = Image.open(WIFI_OFFLINE_PATH)
            self.nowifi_image = Image.new("RGB", wifi_img.size, SPLASH_COLOR)
            self.nowifi_image.paste(wifi_img, (0, 0), wifi_img)  
        except Exception as e:
            print(f"加载图片失败: {e}")
            self.nowifi_image = Image.new("RGB", (100, 100), (255, 0, 0))  
    def _start_button_thread(self):
        def check_button():
            while True:
                if self.button.press_b():
                    try:
                        if self.audio_stream:
                            self.audio_stream.stop()
                            logging.warning('audio_stream kill')
                    except Exception as e:
                        logging.warning(e)
                    try:
                        if self.stream_a:
                            self.stream_a.stop_stream()
                            self.stream_a.close()
                            logging.warning("stream_a kill")
                    except Exception as e:
                        logging.warning(e)
                    try:
                        if self.p:
                            self.p.terminate()
                            logging.warning("p terminate")
                    except:
                        pass
                    print("B键按下, 退出程序")
                    os._exit(0)
                time.sleep(0.1)
        
        thread = threading.Thread(target=check_button, daemon=True)
        thread.start()

    def show_message(self, text, color=(255, 255, 255)):
        self.draw.rectangle((0, 0, self.display.height, self.display.width), fill=SPLASH_COLOR)
        self.draw.text((80, 100), text, fill=color, font=self.font)
        self.display.ShowImage(self.splash)

    def execute_action(self, action_name):
        if action_name in ACTION_MAP:
            action_id, duration = ACTION_MAP[action_name]
            self.dog.action(action_id)
            time.sleep(duration)
            return True
        return False

    def check_network(self):
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                requests.get(TEST_NETWORK_URL, timeout=1)
                print("Net is connected")
                self.network_available = True
                return True  # 直接返回True，不显示任何内容
            except:
                print(f"Network connection attempt {attempt + 1} failed")
                attempt += 1
                time.sleep(1)
        
        print("Network connection failed after 5 attempts")
        self.network_available = False
        self.draw.rectangle((0, 0, self.display.height, self.display.width), fill=SPLASH_COLOR)
        img_width, img_height = self.nowifi_image.size
        x_pos = (self.display.height - img_width) // 2
        y_pos = 40
        self.splash.paste(self.nowifi_image, (x_pos, y_pos))
        if la == "cn":
            text = "WIFI未连接或无网络"
        else:
            text = "WIFI is not connected"
        text_width = self.draw.textlength(text, font=font2)
        x_position = (self.display.height - text_width) // 2
        self.draw.text((x_position, 170), text, fill=color_white, font=font2)
        self.display.ShowImage(self.splash)
        
        return False

    def run(self):
        if not self.check_network():
            while True:
                time.sleep(1)
            return
        
        if la == "cn":
            self.show_message("正在启动，请稍后", color=(255, 255, 255))
        else:
            self.show_message("Starting up...", color=(255, 255, 255))
            
        while True:
            try:
                self.p = pyaudio.PyAudio()
                self.stream_a = self.p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                )
                self.audio_stream = AudiostreamSource()
                logging.warning('音频初始化完成')
                start_recording(self.p, self.stream_a, self.audio_stream)
                logging.warning("录音结束")
                content = test_one()
                
                if not content:
                    print("录音出错")
                    continue
                
                print("识别内容:", content)
                
                action_results = model_output(content=content)
                
                action_executed = False
                for action_name, action_value in zip(ACTION_MAP.keys(), action_results):
                    if int(action_value) == 1:
                        print(f"执行动作: {action_name}")
                        self.execute_action(action_name)
                        action_executed = True
                        break
                
                if not action_executed:
                    if la == "cn":
                        self.show_message("未识别指令")
                    else:
                        self.show_message("Unrecognized command")
                    print("未识别指令")
                    self.dog.reset()
                
                time.sleep(1)

            except KeyboardInterrupt:
                print("程序终止")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                continue

if __name__ == "__main__":
    controller = DogController()
    controller.run()