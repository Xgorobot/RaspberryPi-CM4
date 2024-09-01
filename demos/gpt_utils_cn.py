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

mic_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic.png")
mic_wave = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic_wave.png")
offline_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/offline.png")
draw_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/gpt_draw.png")


def clear_top():
    draw.rectangle([(0, 0), (320, 111)], fill=splash_theme_color)


def clear_bottom():
    draw.rectangle([(0, 111), (320, 240)], fill=splash_theme_color)


def draw_wave(ch):
    if ch > 10:
        ch = 10
    start_x = 40
    start_y = 32
    width, height = 80, 50
    y_center = height // 2
    current_y = y_center
    previous_point = (0 + start_x, y_center + start_y)
    clear_top()
    # draw.rectangle([(0, 0), (320, 240)], fill=splash_theme_color)
    draw.bitmap((145, 40), mic_logo, mic_purple)
    x = 0
    while x < width:
        segment_length = random.randint(7, 25)
        gap_length = random.randint(4, 20)

        for _ in range(segment_length):
            if x >= width:
                break

            amplitude_change = random.randint(-ch, ch)
            current_y += amplitude_change

            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1

            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill=mic_purple)
            previous_point = current_point
            x += 1

        for _ in range(gap_length):
            if x >= width:
                break

            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill=mic_purple, width=2)
            previous_point = current_point
            x += 1

    start_x = 210
    start_y = 32
    width, height = 80, 50
    y_center = height // 2
    current_y = y_center
    previous_point = (0 + start_x, y_center + start_y)
    draw.rectangle(
        [(start_x - 1, start_y), (start_x + width, start_y + height)],
        fill=splash_theme_color,
    )

    x = 0
    while x < width:
        segment_length = random.randint(7, 25)
        gap_length = random.randint(4, 20)

        for _ in range(segment_length):
            if x >= width:
                break

            amplitude_change = random.randint(-ch, ch)
            current_y += amplitude_change

            if current_y < 0:
                current_y = 0
            elif current_y > height - 1:
                current_y = height - 1

            current_point = (x + start_x, current_y + start_y)
            draw.line([previous_point, current_point], fill=mic_purple)
            previous_point = current_point
            x += 1

        for _ in range(gap_length):
            if x >= width:
                break

            current_point = (x + start_x, y_center + start_y)
            draw.line([previous_point, current_point], fill=mic_purple, width=2)
            previous_point = current_point
            x += 1


def draw_cir(ch):
    if ch > 15:
        ch = 15
    clear_top()
    draw.bitmap((145, 40), mic_logo, mic_purple)
    radius = 4
    cy = 60

    centers = [(62, cy), (87, cy), (112, cy), (210, cy), (235, cy), (260, cy)]

    for center in centers:
        random_offset = random.randint(0, ch)
        new_y = center[1] + random_offset
        new_y2 = center[1] - random_offset

        draw.line([center[0], new_y2, center[0], new_y], fill=mic_purple, width=11)

        top_left = (center[0] - radius, new_y - radius)
        bottom_right = (center[0] + radius, new_y + radius)
        draw.ellipse([top_left, bottom_right], fill=mic_purple)
        top_left = (center[0] - radius, new_y2 - radius)
        bottom_right = (center[0] + radius, new_y2 + radius)
        draw.ellipse([top_left, bottom_right], fill=mic_purple)


def draw_wait(j):
    center = (161, 56)
    initial_radius = 50 - j * 8
    clear_top()
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)

        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )

    draw.bitmap(
        (145, 40),
        mic_wave,
    )
    display.ShowImage(splash)


def draw_play():
    j = 0
    center = (161, 56)
    initial_radius = 50 - j * 8
    # draw.rectangle([(40, 0), (240, 120)], fill=splash_theme_color)
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)

        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )

    # draw.bitmap(
    #     (145, 40),
    #     mic_wave,
    # )

    image_height = 50
    line_width = 3
    spacing = 3
    start_x = 146 + spacing
    for _ in range(5):
        line_length = random.randint(3, 20)
        start_y = (image_height - line_length) // 2 + 30
        end_y = start_y + line_length
        draw.line((start_x, start_y, start_x, end_y), fill="white", width=line_width)
        draw.point((start_x, start_y - 1), fill="white")
        draw.point((start_x, end_y + 1), fill="white")
        start_x += line_width + spacing

    display.ShowImage(splash)


def draw_offline():
    draw.bitmap((115, 20), offline_logo, "red")
    warn_text = "Wifi未连接或无网络"
    draw.text((90, 140), warn_text, fill=(255, 255, 255), font=font3)
    display.ShowImage(splash)


def draw_draw(j):
    center = (161, 86)
    initial_radius = 50 - j * 8
    draw.rectangle([(0, 0), (320, 240)], fill=splash_theme_color)
    for i in range(4 - j):
        radius = initial_radius - i * 8
        color_intensity = 223 - (3 - i) * 50
        blue_color = (24, 47, color_intensity)

        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=blue_color,
            fill=blue_color,
            width=2,
        )

    draw.bitmap(
        (147, 72),
        draw_logo,
    )
    display.ShowImage(splash)


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


def wait_anmi(num):
    global play_anmi
    while 1:
        if play_anmi == False:
            break
        draw_wait(3)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_wait(2)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_wait(1)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_wait(0)
        time.sleep(0.4)


def draw_anmi(num):
    global play_anmi
    while 1:
        if play_anmi == False:
            break
        draw_draw(3)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_draw(2)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_draw(1)
        time.sleep(0.4)
        if play_anmi == False:
            break
        draw_draw(0)
        time.sleep(0.4)


def speak_anmi(num):
    global play_anmi
    while 1:
        if play_anmi == False:
            break
        draw_play()
        time.sleep(0.05)


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


def scroll_text_on_lcd(text, x, y, max_lines, delay):
    lines = text.split("\n")
    total_lines = len(lines)
    for i in range(total_lines - max_lines):
        lcd_rect(0, 110, 320, 240, splash_theme_color, -1)
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
    play_wait_anmi1 = threading.Thread(target=wait_anmi, args=(0,))
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
            draw_wave(int(vol / 10000))
            display.ShowImage(splash)
        audio_stream.stop()
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
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
            draw_cir(int(vol / 10000))
            display.ShowImage(splash)
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


def start_audio_camera(timel=3, save_file="test.wav"):
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
            draw_wave(int(vol / 10000))
            display.ShowImage(splash)
        audio_stream.stop()
        print("take a photo")
        time.sleep(0.5)
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        path = "/home/pi/xgoPictures/"
        success, image = cap.read()
        filename = "rec"
        cv2.imwrite(path + filename + ".jpg", image)
        if not success:
            print("Ignoring empty camera frame")
        image = cv2.resize(image, (320, 240))
        b, g, r = cv2.split(image)
        image = cv2.merge((r, g, b))
        image = cv2.flip(image, 1)
        imgok = Image.fromarray(image)
        display.ShowImage(imgok)
        time.sleep(1)
        cap.release()
        cv2.destroyAllWindows()
        print("camera close")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        display.ShowImage(splash)
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
            draw_cir(int(vol / 10000))
            display.ShowImage(splash)
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


def line_break(line):
    LINE_CHAR_COUNT = 19 * 2
    CHAR_SIZE = 20
    TABLE_WIDTH = 4
    ret = ""
    width = 0
    for c in line:
        if len(c.encode("utf8")) == 3:
            if LINE_CHAR_COUNT == width + 1:
                width = 2
                ret += "\n" + c
            else:
                width += 2
                ret += c
        else:
            if c == "\t":
                space_c = TABLE_WIDTH - width % TABLE_WIDTH
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


def gpt_draw(scr):
    global quitmark
    global play_anmi
    play_anmi = True
    play_wait_anmi1 = threading.Thread(target=draw_anmi, args=(0,))
    play_wait_anmi1.start()
    APPID = "204e2232"
    APISecret = "MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2"
    APIKEY = "1896d14df5cd043b25a7bc6bee426092"
    desc = scr
    res = draw_main(
        desc,
        appid="204e2232",
        apikey="1896d14df5cd043b25a7bc6bee426092",
        apisecret="MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2",
    )
    parser_Message(res)
    original_image_path = "original.jpg"
    resized_image_path = "resized.jpg"
    resize_image(original_image_path, resized_image_path)
    play_anmi = False
    time.sleep(0.5)
    image = Image.open("resized.jpg")
    splash.paste(image, (0, 0))
    display.ShowImage(splash)
    if quitmark == 1:
        print("main quit")
        return 0
    draw.rectangle([(0, 0), (320, 240)], fill=splash_theme_color)

    time.sleep(5.5)


def gpt_rec(speech_text):
    global play_anmi
    play_anmi = True
    play_wait_anmi1 = threading.Thread(target=wait_anmi, args=(0,))
    play_wait_anmi1.start()
    global answer
    appid = "204e2232"  # 填写控制台中获取的 APPID 信息
    api_secret = "MDJjYzQ3NmJmODY2MmVlMDdhMDdlMjA2"  # 填写控制台中获取的 APISecret 信息
    api_key = "1896d14df5cd043b25a7bc6bee426092"  # 填写控制台中获取的 APIKey 信息

    imageunderstanding_url = (
        "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"  # 云端环境的服务地址
    )
    imagedata = open("/home/pi/xgoPictures/rec.jpg", "rb").read()
    texturl = [
        {
            "role": "user",
            "content": str(base64.b64encode(imagedata), "utf-8"),
            "content_type": "image",
        }
    ]
    question = checklen(getText("user", speech_text))
    answer = ""
    main(appid, api_key, api_secret, imageunderstanding_url, question)
    getText("assistant", answer)
    print(answer)
    play_anmi = False
    return answer


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
    play_wait_anmi2 = threading.Thread(target=wait_anmi, args=(0,))
    play_wait_anmi2.start()
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
    play_anmi = True
    play_wait_anmi = threading.Thread(target=speak_anmi, args=(0,))
    play_wait_anmi.start()
    proc = Popen("mplayer tts.mp3", shell=True)
    proc.wait()
    time.sleep(0.5)
    play_anmi = False


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
    digest = base64.b64encode(sha256.digest()).decode(encoding="utf-8")
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3 :]
    schema = requset_url[: stidx + 3]
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
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(
        host, date, method, path
    )
    # print(signature_origin)
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")
    authorization_origin = (
        'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
        % (api_key, "hmac-sha256", "host date request-line", signature_sha)
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
        encoding="utf-8"
    )
    # print(authorization_origin)
    values = {"host": host, "date": date, "authorization": authorization}

    return requset_url + "?" + urlencode(values)


# 生成请求body体
def getBody(appid, text):
    body = {
        "header": {"app_id": appid, "uid": "123456789"},
        "parameter": {
            "chat": {"domain": "general", "temperature": 0.5, "max_tokens": 4096}
        },
        "payload": {"message": {"text": [{"role": "user", "content": text}]}},
    }
    return body


# 发起请求并返回结果
def draw_main(text, appid, apikey, apisecret):
    host = "http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti"
    url = assemble_ws_auth_url(
        host, method="POST", api_key=apikey, api_secret=apisecret
    )
    content = getBody(appid, text)
    print(time.time())
    response = requests.post(
        url, json=content, headers={"content-type": "application/json"}
    ).text
    print(time.time())
    return response


# 将base64 的图片数据存在本地
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
    code = data["header"]["code"]
    if code != 0:
        print(f"请求错误: {code}, {data}")
    else:
        text = data["payload"]["choices"]["text"]
        imageContent = text[0]
        # if('image' == imageContent["content_type"]):
        imageBase = imageContent["content"]
        imageName = data["header"]["sid"]
        savePath = f"original.jpg"
        base64_to_image(imageBase, savePath)
        print("图片保存路径：" + savePath)


# 星火图片理解demo
import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client


class Ws_Param_Pic(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, imageunderstanding_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(imageunderstanding_url).netloc
        self.path = urlparse(imageunderstanding_url).path
        self.ImageUnderstanding_url = imageunderstanding_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )

        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": self.host}
        # 拼接鉴权参数，生成url
        url = self.ImageUnderstanding_url + "?" + urlencode(v)
        # print(url)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error_pic(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close_pic(ws, one, two):
    print(" ")


# 收到websocket连接建立的处理
def on_open_pic(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, question=ws.question))
    ws.send(data)


# 收到websocket消息的处理
def on_message_pic(ws, message):
    # print(message)
    data = json.loads(message)
    code = data["header"]["code"]
    if code != 0:
        print(f"请求错误: {code}, {data}")
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content, end="")
        global answer
        answer += content
        # print(1)
        if status == 2:
            ws.close()


def gen_params(appid, question):
    """
    通过appid和用户的提问来生成请参数
    """

    data = {
        "header": {"app_id": appid},
        "parameter": {
            "chat": {
                "domain": "image",
                "temperature": 0.5,
                "top_k": 4,
                "max_tokens": 2028,
                "auditing": "default",
            }
        },
        "payload": {"message": {"text": question}},
    }

    return data


def main(appid, api_key, api_secret, imageunderstanding_url, question):
    print("understanding")
    print(appid, api_key, api_secret)
    imageunderstanding_url = (
        "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"  # 云端环境的服务地址
    )
    imagedata = open("/home/pi/xgoPictures/rec.jpg", "rb").read()
    texturl = [
        {
            "role": "user",
            "content": str(base64.b64encode(imagedata), "utf-8"),
            "content_type": "image",
        }
    ]

    wsParam = Ws_Param_Pic(appid, api_key, api_secret, imageunderstanding_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(
        wsUrl,
        on_message=on_message_pic,
        on_error=on_error_pic,
        on_close=on_close_pic,
        on_open=on_open_pic,
    )
    ws.appid = appid
    # ws.imagedata = imagedata
    ws.question = question
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


def getText(role, content):
    imagedata = open("/home/pi/xgoPictures/rec.jpg", "rb").read()
    texturl = [
        {
            "role": "user",
            "content": str(base64.b64encode(imagedata), "utf-8"),
            "content_type": "image",
        }
    ]
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    texturl.append(jsoncon)
    return texturl


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    # print("text-content-tokens:", getlength(text[1:]))
    while getlength(text[1:]) > 8000:
        del text[1]
    return text
