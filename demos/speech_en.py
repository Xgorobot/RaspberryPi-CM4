from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

from xgolib import XGO
import cv2
import os, socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from key import Button
import threading

import pyaudio
import wave

import numpy as np
from scipy import fftpack

from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command, default_libpath

from openai import OpenAI

clash_port = os.getenv("CLASH_PORT")

if clash_port is not None:
    os.environ["http_proxy"] = clash_port
    os.environ["https_proxy"] = clash_port

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2
xunfei = ""


def SpeechRecognition():
    client = OpenAI()
    print("gpt transcript")
    AUDIO_FILE = "test.wav"
    audio_file = open(AUDIO_FILE, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    print(transcript)
    return transcript.text


def start_audio(timel=3, save_file="test.wav"):
    global automark, quitmark
    start_threshold = 60000
    end_threshold = 40000
    endlast = 10
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 8000
    RECORD_SECONDS = timel
    WAVE_OUTPUT_FILENAME = save_file

    if automark:
        p = pyaudio.PyAudio()
        print("正在聆听")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw,
            35,
            40,
            "Listening...",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
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
            draw,
            35,
            40,
            "Press b to start",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
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
                    "Listening...",
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
        draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw,
            35,
            48,
            "Record done",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
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


# define colors
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
display.Init()
display.clear()

# font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc", 15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 16)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc", 24)
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


def mode(num):
    start = 120
    lcd_rect(start, 0, 200, 19, splash_theme_color, -1)
    lcd_draw_string(
        draw, start, 0, "Auto Mode", color=(255, 0, 0), scale=font2, mono_space=False
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
                    "Auto Mode",
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
                    "Manual Mode",
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


def actions(act):
    commandlist = [
        "Go forward",
        "Go back",
        "Turn left",
        "Turn right",
        "Left translation",
        "Right translation",
        "Dance",
        "Push up",
        "Take a pee",
        "Sit down",
        "Wave hand",
        "Stretch",
        "Hand shake",
        "Pray",
        "Looking for food",
        "Chicken head",
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
        time.sleep(3)
    else:
        time.sleep(1)
        print("command not find")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw,
            35,
            48,
            "Error in command",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
        )
        display.ShowImage(splash)
        dog.reset()
        time.sleep(0.5)


import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    # draw.line((2,98,318,98), fill=(255,255,255), width=2)
    draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
    lcd_draw_string(
        draw,
        57,
        100,
        "Please say the following:",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        130,
        "Go forward|Go back|Turn left|Turn right",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        150,
        "Left translation|Right translation|Dance",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        170,
        "Push up|Take a pee|Sit down|Wave hand",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        190,
        "Stretch|Hand shake|Pray",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        210,
        "Looking for food|Chicken head",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)

    # time.sleep(2)
    while 1:
        start_audio()
        if quitmark == 0:
            xunfei = ""
            lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
            draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
            lcd_draw_string(
                draw,
                35,
                48,
                "Waiting for identifying",
                color=(255, 0, 0),
                scale=font3,
                mono_space=False,
            )
            display.ShowImage(splash)
            try:
                speech_text = SpeechRecognition()
            except:
                speech_text = ""
            xunfei = speech_text
            lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
            draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
            lcd_draw_string(
                draw, 35, 48, xunfei, color=(255, 0, 0), scale=font3, mono_space=False
            )
            display.ShowImage(splash)
            actions(xunfei)
        if quitmark == 1:
            print("main quit")
            break

else:
    lcd_draw_string(
        draw,
        57,
        70,
        "XGO is offline,please check your network settings",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        57,
        120,
        "Press C to exit",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)
    while 1:
        if button.press_b():
            break
