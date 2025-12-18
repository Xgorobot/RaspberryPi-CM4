import os,random
import time
import wave
import numpy as np
import pyaudio
import datetime
from scipy import fftpack
from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command, default_libpath
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch
import logging
from key import language
la=language()
mic_logo = Image.open("/home/jinliang/RaspberryPi-CM4-main/pics/mic.png")
mic_wave = Image.open("/home/jinliang/RaspberryPi-CM4-main/pics/mic_wave.png")
mic_purple = (24, 47, 223)
splash_theme_color = (15, 21, 46)
font2=ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
quitmark = 0
automark = True

#version=2.0
# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)


def visual(content):
    gray_color = (128, 128, 128)
    rectangle_x = (display.width - 120) // 2 
    rectangle_y = 110  
    rectangle_width = 200
    rectangle_height = 80
    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height),
                   fill=gray_color)
    def lcd_draw_string(
            splash,
            x,
            y,
            text,
            color=(255, 255, 255),
            font_size=16,
            max_width=220,
            max_lines=5,
            clear_area=False
    ):
        font = ImageFont.truetype("/home/jinliang/model/msyh.ttc", font_size)
        line_height = font_size + 2
        total_height = max_lines * line_height
        if clear_area:
            draw.rectangle((x, y, x + max_width, y + total_height), fill=(15, 21, 46))
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        if max_lines:
            lines = lines[:max_lines]

        for i, line in enumerate(lines):
            splash.text((x, y + i * line_height), line, fill=color, font=font)

    lcd_draw_string(
        draw,
        x=70,
        y=115,
        text=content,
        color=(255, 255, 255),
        font_size=16,
        max_width=190,
        max_lines=5,
        clear_area=False
    )
'''
    LCD Rect
'''
def lcd_rect(x, y, w, h, color, thickness):
    draw.rectangle([(x, y), (w, h)], fill=color, width=thickness)
def clear_top():
    draw.rectangle([(0, 0), (320, 111)], fill=splash_theme_color)
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

'''
    Draw Cir
'''
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

def start_recording(p, stream_a, audio_stream, timel=3, save_file="recorded_audio.wav"):
    global automark, quitmark
    start_threshold = 120000
    end_threshold = 40000
    endlast = 15
    max_record_time = 8 
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = save_file

    if automark:
        logging.warning(automark)
        frames = []
        start_luyin = False
        break_luyin = False
        data_list = [0] * endlast
        sum_vol = 0
        start_time = None

        libpath = "/home/jinliang/RaspberryPi-CM4-main/demos/speech/src/libnyumaya_premium.so.3.1.0"
        extractor = FeatureExtractor(libpath)
        detector = AudioRecognition(libpath)
        extactor_gain = 1.0
        keywordIdlulu = detector.addModel("/home/jinliang/RaspberryPi-CM4-main/demos/speech/src/lulu_v3.1.907.premium", 0.7)
        bufsize = detector.getInputDataSize()

        audio_stream.start()
        audio_stream.buffer = None
        while not break_luyin:
            if not automark or quitmark == 1:
                break
            
            frame = audio_stream.read(bufsize * 2, bufsize * 2)
            if not frame:
                continue
            features = extractor.signalToMel(frame, extactor_gain)
            prediction = detector.runDetection(features)
            if prediction == keywordIdlulu:
                logging.warning("lulu detected: " + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
                os.system("aplay /home/jinliang/RaspberryPi-CM4-main/demos/speech/voice/ding.wav")
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
            if la=="cn":
              visual(content='请说:“你好，lulu”唤醒机器人')
            else:
              visual(content="Please say: 'Hello,lulu' to wake up the robot.")
            display.ShowImage(splash)
        
        audio_stream.stop()
        logging.warning("wakeup")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        
        while not break_luyin:
            if not automark or quitmark == 1:
                break
            
            data = stream_a.read(CHUNK, exception_on_overflow=False)
            rt_data = np.frombuffer(data, dtype=np.int16)
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
            vol = sum(fft_data) // len(fft_data)
            
            data_list.pop(0)
            data_list.append(vol)
            
            logging.warning(f"当前音量: {vol}, 启动阈值: {start_threshold}, 结束阈值: {end_threshold}")
            
            if vol > start_threshold:
                sum_vol += 1
                if sum_vol == 1:
                    print("start recording")
                    start_luyin = True
                    start_time = time.time()
            
            if start_luyin:
                elapsed_time = time.time() - start_time
                
                if all(float(i) < end_threshold for i in data_list) or elapsed_time > max_record_time:
                    print("录音结束: 低音量 或 录音时间超限")
                    break_luyin = True
                    frames = frames[:-5]
            
            if start_luyin:
                frames.append(data)
            print(start_threshold, vol)
            draw_cir(int(vol / 10000))
            if la=="cn":
              visual(content='唤醒成功，请下达指令')
            else:
              visual(content='Wake-up successful, please issue command.')
            display.ShowImage(splash)
        print("auto end")
    
    if quitmark == 0:
        try:
            stream_a.stop_stream()
            stream_a.close()
            logging.warning("stream_a stop")
        except:
            pass
        p.terminate()
        logging.warning("p kill")
        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()
        print(f"录音完成，文件已保存: {WAVE_OUTPUT_FILENAME}")

if __name__ == "__main__":
    start_recording()
