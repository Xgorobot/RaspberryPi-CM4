from openai import OpenAI
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

clash_port = os.getenv("CLASH_PORT")
print(clash_port)

if clash_port is not None:
    os.environ["http_proxy"] = clash_port
    os.environ["https_proxy"] = clash_port

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
            draw,
            35,
            40,
            "Record done!",
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


def download_image(url, save_path):
    response = requests.get(url)

    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Image downloaded successfully and saved at {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")


def resize_image(image_path, output_path, size=(320, 240)):
    with Image.open(image_path) as img:
        img_resized = img.resize(size)
        img_resized.save(output_path)
        print(f"Image resized successfully and saved at {output_path}")


def SpeechRecognition():
    client = OpenAI()
    audio_file = open("test.wav", "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", file=audio_file, response_format="text"
    )

    print(transcript)
    return transcript


def gpt_draw(scr):
    global quitmark
    client = OpenAI()
    response = client.images.generate(
        model="dall-e-3",
        prompt=scr,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    if quitmark == 1:
        print("main quit")
        return 0
    image_url = response.data[0].url
    print(image_url)
    original_image_path = "original.jpg"
    resized_image_path = "resized.jpg"
    download_image(image_url, original_image_path)
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

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
    display.ShowImage(splash)

    while 1:
        start_audio()
        if quitmark == 0:
            xunfei = ""
            lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
            draw.rectangle((20, 30, 300, 80), splash_theme_color, "white", width=3)
            lcd_draw_string(
                draw,
                35,
                40,
                "Recognizing",
                color=(255, 0, 0),
                scale=font3,
                mono_space=False,
            )
            display.ShowImage(splash)
            speech_text = SpeechRecognition()
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
                        "Waiting for chatGPT",
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
