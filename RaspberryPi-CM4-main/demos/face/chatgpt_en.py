import sys
sys.path.append("/home/pi/RaspberryPi-CM4-main/demos")
import os,math
from xgolib import XGO
import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import threading
from subprocess import Popen

from libnyumaya import AudioRecognition, FeatureExtractor
from auto_platform import AudiostreamSource, play_command,default_libpath
from datetime import datetime

from openai import OpenAI
from face.eye_mouth_controller import start_speaking, stop_speaking

os.environ["http_proxy"] = "http://192.168.157.6:7890"
os.environ["https_proxy"] = "http://192.168.157.6:7890"


import pyaudio
import wave

import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU 

xgo = XGOEDU()

btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)
#display init
display = LCD_2inch.LCD_2inch()
#display.Init()
display.clear()

#font
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc",15)
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",16)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc",18)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

quitmark=0
automark=True
button=Button()

def action(num):
    global quitmark
    while quitmark==0:
        time.sleep(0.01)
        if button.press_b():
            quitmark=1

def mode(num):
    start=120
    lcd_rect(start,0,300,19,splash_theme_color,-1)
    lcd_draw_string(draw,start,0, "Auto Mode", color=(255,0,0), scale=font2, mono_space=False)
    display.ShowImage(splash)
    global automark,quitmark
    while quitmark==0:
        time.sleep(0.01)
        if button.press_c():
            automark=not automark
            if automark:
                lcd_rect(start,0,300,19,splash_theme_color,-1)
                lcd_draw_string(draw,start,0, "Auto Mode", color=(255,0,0), scale=font2, mono_space=False)
                display.ShowImage(splash)
            else:
                lcd_rect(start,0,300,19,splash_theme_color,-1)
                lcd_draw_string(draw,start,0, "Manual Mode", color=(255,0,0), scale=font2, mono_space=False)
                display.ShowImage(splash)
            print(automark)

mode_button = threading.Thread(target=mode, args=(0,))
mode_button.start()

check_button = threading.Thread(target=action, args=(0,))
check_button.start()

def scroll_text_on_lcd(text, x, y, max_lines, delay):
    lines = text.split('\n')
    total_lines = len(lines)
    for i in range(total_lines - max_lines):
        lcd_rect(0,90,320,290,splash_theme_color,-1)
        visible_lines = lines[i:i + max_lines - 1]
        last_line = lines[i + max_lines - 1]

        for j in range(max_lines - 1):
            lcd_draw_string(draw,x, y + j*20,visible_lines[j],color=(255,255,255), scale=font2, mono_space=False)
        lcd_draw_string(draw, x, y + (max_lines - 1)*20,last_line,color=(255,255,255), scale=font2, mono_space=False)

        display.ShowImage(splash)
        time.sleep(delay)

def get_wav_duration():
    filename='test.wav'
    with wave.open(filename, 'rb') as wav_file:
        # 获取帧数和采样率
        n_frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        
        # 计算持续时间
        duration = n_frames / frame_rate
        return duration

def tts(content):
    client = OpenAI()
    speech_file_path = "speech.mp3"
    response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=content
    )
    response.stream_to_file(speech_file_path)
    proc=Popen("mplayer speech.mp3", shell=True)
    dog.rider_led(1,[0,255,0])
    dog.rider_led(0,[0,255,0])
    time.sleep(0.5)
    thread = start_speaking(content)
    stop_speaking(thread)

def gpt(speech_text):
    client = OpenAI()
    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": speech_text}
    ]
    )
    re=response.choices[0].message.content
    return re


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
        print("I am listening")
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,40, "I am listening...", color=(255,0,0), scale=font3, mono_space=False)
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
        dog.rider_led(1,[0,0,255])
        dog.rider_led(0,[0,0,255])
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
                if sum_vol==1:
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
        lcd_draw_string(draw,35,40, "Record done!", color=(255,0,0), scale=font3, mono_space=False)
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

def SpeechRecognition():
    client = OpenAI()
    print('gpt transcript')
    AUDIO_FILE = 'test.wav' 
    audio_file = open(AUDIO_FILE, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    print(transcript)
    return transcript.text


def line_break(line):
    LINE_CHAR_COUNT = 19*2  
    CHAR_SIZE = 20
    TABLE_WIDTH = 4
    ret = ''
    width = 0
    for c in line:
        if len(c.encode('utf8')) == 3:  
            if LINE_CHAR_COUNT == width + 1: 
                width = 2
                ret += '\n' + c
            else: 
                width += 2
                ret += c
        else:
            if c == '\t':
                space_c = TABLE_WIDTH - width % TABLE_WIDTH  
                ret += ' ' * space_c
                width += space_c
            elif c == '\n':
                width = 0
                ret += c
            else:
                width += 1
                ret += c
        if width >= LINE_CHAR_COUNT:
            ret += '\n'
            width = 0
    if ret.endswith('\n'):
        return ret
    return ret + '\n'

def split_string(text):
    import re
    seg=30
    result = []
    current_segment = ""
    current_length = 0

    for char in text:
        is_chinese = bool(re.match(r'[\u4e00-\u9fa5]', char))

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
net=False
try:
    html = requests.get("http://www.baidu.com",timeout=2)
    net=True
except:
    net=False

if net:
    dog = XGO(port='/dev/ttyAMA0',version="xgolite")
    draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
    display.ShowImage(splash)
        
    while 1:
        start_audio()
        dog.rider_led(1,[0,0,0])
        dog.rider_led(0,[0,0,0])
        if quitmark==0:
            xunfei=''
            lcd_rect(30,40,320,90,splash_theme_color,-1)
            draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
            lcd_draw_string(draw,35,40, "Recognizing", color=(255,0,0), scale=font3, mono_space=False)
            display.ShowImage(splash)
            try:
                speech_text=SpeechRecognition()
            except:
                speech_text=''
            if speech_text!='':
              speech_list=split_string(speech_text)
              print(speech_list)
              for sp in speech_list:
                  lcd_rect(0,40,320,290,splash_theme_color,-1)
                  draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
                  lcd_draw_string(draw,35,40,sp, color=(255,0,0), scale=font3, mono_space=False)
                  lcd_draw_string(draw,27,90, "Waiting for OPENAI...", color=(255,255,255), scale=font2, mono_space=False)
                  display.ShowImage(splash)
                  time.sleep(1.5)
              re=gpt(speech_text)
              re_e=line_break(re)
              print(re_e)
              lcd_rect(0,40,320,290,splash_theme_color,-1)
              draw.rectangle((20,30,300,80), splash_theme_color, 'white',width=3)
              lcd_draw_string(draw,10,90, re_e, color=(255,255,255), scale=font2, mono_space=False)
              display.ShowImage(splash)
              lines=len(re_e.split('\n'))
              tick=0.3
              if lines>6:
                  scroll_text_on_lcd(re_e, 10, 90, 7, tick)
              tts(re)
              dog.rider_led(1,[0,0,0])
              dog.rider_led(0,[0,0,0])
            
            
        if quitmark==1:
            print('main quit')
            break

else:
    lcd_draw_string(draw,57,70, "XGO is offline,please check your network settings", color=(255,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,57,120, "Press C to exit", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    while 1:
        if button.press_b():
            break

