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


mic_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic.png")
mic_wave = Image.open("/home/pi/RaspberryPi-CM4-main/pics/mic_wave.png")
mic_purple = (24, 47, 223)
splash_theme_color = (15, 21, 46)
font2=ImageFont.truetype("/home/pi/model/msyh.ttc", 16)
quitmark = 0
automark = True


# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

def lcd_draw_string(splash, x, y, text, color=(255, 255, 255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0, 0, 0)):
    splash.text((x, y), text, fill=color, font=scale)

def show_words_dog():
    lcd_draw_string(draw, 10, 150, "Dance|PushUp|Pee|Strech|Pray|Beg", color=(0, 255, 255), scale=font2, mono_space=False)
    lcd_draw_string(draw, 10, 170, "LookingForFood|GrabDown|Wave", color=(0, 255, 255), scale=font2, mono_space=False)
    lcd_draw_string(draw, 10, 190, "ChickenHead", color=(0, 255, 255), scale=font2, mono_space=False)


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

def start_recording(timel=3, save_file="recorded_audio.wav"):
    global automark, quitmark
    start_threshold = 120000
    end_threshold = 40000
    endlast = 15
    max_record_time = 5
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
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
        start_time = None
        
        audio_stream = AudiostreamSource()
        libpath = "/home/pi/RaspberryPi-CM4-main/demos/speechEn/src/libnyumaya_premium.so.3.1.0"
        extractor = FeatureExtractor(libpath)
        detector = AudioRecognition(libpath)
        extactor_gain = 1.0
        keywordIdlulu = detector.addModel("/home/pi/RaspberryPi-CM4-main/demos/speechEn/src/lulu_v3.1.907.premium", 0.7)
        bufsize = detector.getInputDataSize()
        
        audio_stream.start()

        while not break_luyin:
            if not automark or quitmark == 1:
                break
            
            frame = audio_stream.read(bufsize * 2, bufsize * 2)
            if not frame:
                continue
            features = extractor.signalToMel(frame, extactor_gain)
            prediction = detector.runDetection(features)
            if prediction == keywordIdlulu:
                print("lulu detected: " + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
                os.system("aplay /home/pi/RaspberryPi-CM4-main/demos/speechEn/voice/ding.wav")
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
            show_words_dog()
            display.ShowImage(splash)
        
        audio_stream.stop()
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
            
            print(f"当前音量: {vol}, 启动阈值: {start_threshold}, 结束阈值: {end_threshold}")
            
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
            show_words_dog()
            display.ShowImage(splash)
        print("auto end")
    
    if quitmark == 0:
        try:
            stream_a.stop_stream()
            stream_a.close()
        except:
            pass
        p.terminate()
        
        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()
        print(f"录音完成，文件已保存: {WAVE_OUTPUT_FILENAME}")

if __name__ == "__main__":
    start_recording()
