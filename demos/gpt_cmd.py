import os,re
import openai
from xgolib import XGO
import cv2
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import threading
import json,base64

import pyaudio
import wave

import numpy as np
from scipy import fftpack

from xgoedu import XGOEDU 

xgo = XGOEDU()

prompt='''
【Role】Please play the role of an experienced robot developer. You are an expert in Raspberry Pi, robotics, and Python development.
【Task】Generate Python code based on command words for the robot dog using the provided Python library.
【Requirements】The Python code, which is automatically generated based on command words, must output a document in MD format.

The specific Python library is as follows, the Python control interface for the robot dog, including: forward, backward, left shift, right shift, rotate, translate and rotate along the XYZ axis, and perform action groups.
xgo.move_x(step)  #The unit of step is millimeters. Positive is forward, negative is backward, 0 means stop, and the range is [-25,25]mm.
xgo.move_y(step)  #The unit of step is millimeters. Positive is left shift, negative is right shift, 0 means stop, and the range is [-18,18]mm.
xgo.turn(speed)  #Speed is the angular velocity, positive is clockwise, negative is counterclockwise, 0 means stop, and the range is [-150,150].
xgo.pace(mode) #Mode is slow, normal, or high. This represents the pace of the robot dog.
time.sleep(X) #The unit of X is seconds, which indicates the duration of the previous instruction.
xgo.action(id) #id is the action group interface, id ranges from 1-24, corresponding to [lie down, stand up, crawl ,turn around, squat, Turn roll, Turn pitch, Turn yaw, 3 axis motion, tke a pee, sit down, wave hand, stretch, wave body, wave side, pray, looking for food, handshake, Chicken head, push-up,seek,dance,Naughty], i.e. the id for lie down is 1, crawl is 4, pray is 18, grab up is 129 , grab mid is 130 , grab down is 130.
xgo.translation(direction, data)  #The value of direction is 'x', 'y', 'z'. The unit of data is millimeters. Positive along the X-axis means forward, 0 means return to the initial position, and negative along the X-axis means backward. The range is [-35,35]mm. The same applies to the y-axis and z-axis.
xgo.attitude(direction, data)  #The value of direction is 'r', 'p', 'y'. The unit of data is degrees. Positive along the X-axis means clockwise rotation, 0 means return to the initial position, and negative along the X-axis means counterclockwise rotation. The range is [-20,20]mm. The same applies to rotation along the y-axis and z-axis.
arm( arm_x, arm_z) #The range for arm_x is [-80,155] and the range for arm_z is [-95,155]
claw(pos) #The range for pos is 0-255, where 0 means the claw is fully open, 255 means the claw is fully closed.
imu(mode) #The value for mode is 0 or 1, 0 means turn off self-stabilization mode, 1 means turn on self-stabilization mode.
reset()#
lcd_picture(filename)   #This function is used for the robot dog to display expressions, such as attack, anger, disgust, like, naughty, pray, sad, sensitive, sleepy, apologize, surprise.
xgoSpeaker(filename)  #This function is used for the robot dog to bark, such as attack, anger, disgust, like, naughty, pray, sad, sensitive, sleepy, apologize, surprise.
I hope you can generate the corresponding motion code using the above functions according to my command.

Below are some examples in the form of (command, code):

Please add the following two initialization codes before each program
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO("xgolite")
XGO_edu = XGOEDU()

Example 1
Command: Move forward for 5 seconds
Code:
from xgolib import XGO
xgo=XGO("xgolite")
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)

Example 2
Command: Shift left for 5 seconds
Code:
from xgolib import XGO
xgo=XGO("xgolite")
xgo.move_y(15)
time.sleep(5)
xgo.move_y(0)

Example 3
Command: Rotate at an angular velocity of 100 for 3 seconds
Code:
from xgolib import XGO
xgo=XGO("xgolite")
xgo.turn(100)
time.sleep(3)
xgo.turn(0)

Example 4
Command: Move forward for 3 seconds, urinate, turn left for 3 seconds, show mechanical arm
from xgolib import XGO
xgo=XGO("xgolite")
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)
xgo.action(11)
xgo.turn(100)
time.sleep(3)
xgo.turn(0)
xgo.action(20)

Example 5
Command: Display a happy expression, then stretch
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO("xgolite")
XGO_edu = XGOEDU()


xgo.action(14)
time.sleep(3)
XGO_edu.lcd_picture(like) 
The example has ended. Please provide Python code based on the commands, with comments included within the code. The final statement should be xgo.reset() to reset it. You must output the document in Markdown format.
'''

quitmark=0
button=Button()

def action(num):
    global quitmark
    while quitmark==0:
        time.sleep(0.01)
        if button.press_b():
            quitmark=1

check_button = threading.Thread(target=action, args=(0,))
check_button.start()

#os.environ["http_proxy"] = "http://192.168.31.203:7890"
#os.environ["https_proxy"] = "http://192.168.31.203:7890"

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
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc",17)
font3 = ImageFont.truetype("/home/pi/model/msyh.ttc",20)
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)
    
openai.api_key = "***"

def gpt(speech_text):
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
    {"role": "system", "content": prompt},
    {"role": "user", "content": speech_text}
    ]
    )

    res=completion.choices[0].message
    return res["content"]

def start_audio(time = 3,save_file="recog.wav"):
    global quitmark
    start_threshold=30000
    end_threshold=8000
    endlast=10     
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = time 
    WAVE_OUTPUT_FILENAME = path="/home/pi/xgoMusic/"+save_file  

    p = pyaudio.PyAudio()   
    print("recording...")
    lcd_rect(30,20,320,90,splash_theme_color,-1)
    draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
    lcd_draw_string(draw,35,28, "Ready for Recording", color=(255,0,0), scale=font3, mono_space=False)
    display.ShowImage(splash)
    
    
    stream = p.open(format=FORMAT,
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
        if quitmark==1:
            print('main quit')
            break
        data = stream.read(CHUNK)
        rt_data = np.frombuffer(data,dtype=np.int16)
        fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
        fft_data = np.abs(fft_temp_data)[0:fft_temp_data.size // 2 + 1]
        vol=sum(fft_data) // len(fft_data)
        data_list.pop(0)
        data_list.append(vol)
        if vol>start_threshold:
            sum_vol+=1
            if sum_vol==2:
                print('start recording')
                start_luyin=True
        if start_luyin :
            kkk= lambda x:float(x)<start_threshold
            if all([kkk(i) for i in data_list]):
                break_luyin =True
                frames=frames[:-5]
        if start_luyin:
            frames.append(data)
    
    print('auto end')

    if quitmark==0:
        lcd_rect(30,40,320,90,splash_theme_color,-1)
        draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
        lcd_draw_string(draw,35,48, "RECORDING DONE!", color=(255,0,0), scale=font3, mono_space=False)
        display.ShowImage(splash)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')  
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

def SpeechRecognition():
    AUDIO_FILE = 'recog.wav' 
    path="/home/pi/xgoMusic/"
    audio_file = open(path+AUDIO_FILE, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]


def line_break(line):
    LINE_CHAR_COUNT = 19*2  # 每行字符数：30个中文字符(=60英文字符)
    CHAR_SIZE = 20
    TABLE_WIDTH = 4
    ret = ''
    width = 0
    for c in line:
        if len(c.encode('utf8')) == 3:  # 中文
            if LINE_CHAR_COUNT == width + 1:  # 剩余位置不够一个汉字
                width = 2
                ret += '\n' + c
            else: # 中文宽度加2，注意换行边界
                width += 2
                ret += c
        else:
            if c == '\t':
                space_c = TABLE_WIDTH - width % TABLE_WIDTH  # 已有长度对TABLE_WIDTH取余
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

def split_string(text):
    import re
    seg=28
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

# re_e='''
# This is line 1.
# This is line 2.
# This is line 3.
# This is line 4.
# This is line 5.
# This is line 6.
# This is line 7.
# This is line 8.
# '''
# scroll_text_on_lcd(re_e, 10, 90, 6, 0.5)


import requests
net=False
try:
    html = requests.get("http://www.baidu.com",timeout=2)
    print('net')
    net=True
except:
    pass

if net:
    dog = XGO(port='/dev/ttyAMA0',version="xgolite")
    #draw.line((2,98,318,98), fill=(255,255,255), width=2)
    draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
    display.ShowImage(splash)
        
    #time.sleep(2)
    while 1:
        start_audio()
        if quitmark==0:
            lcd_rect(0,0,320,290,splash_theme_color,-1)
            draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
            lcd_draw_string(draw,35,28, "Identifying...", color=(255,0,0), scale=font3, mono_space=False)
            display.ShowImage(splash)
            speech_text=SpeechRecognition()
            speech_list=split_string(speech_text)
            print(speech_list)
            for sp in speech_list:
                lcd_rect(0,0,320,290,splash_theme_color,-1)
                draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
                lcd_draw_string(draw,35,28,sp, color=(255,0,0), scale=font2, mono_space=False)
                lcd_draw_string(draw,27,90, "WAIT FOR CHATGPT...", color=(255,255,255), scale=font2, mono_space=False)
                display.ShowImage(splash)
                time.sleep(0.7)
            res=gpt(speech_text)
            re_e=line_break(res)
            print(re_e)
            if re_e!='':
                lcd_rect(0,0,320,290,splash_theme_color,-1)
                draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
                lcd_draw_string(draw,35,28, "MAKING CODE...", color=(255,0,0), scale=font3, mono_space=False)
                lcd_draw_string(draw,10,90, re_e, color=(255,255,255), scale=font2, mono_space=False)
                display.ShowImage(splash)
                with open("cmd.py", "w") as file:
                    code_blocks = re.findall(r'```python(.*?)```', res, re.DOTALL)
                    extracted_code = []
                    for block in code_blocks:
                        code_lines = block.strip().split('\n')
                        extracted_code.append("\n".join(code_lines))  # Include all lines, including the first one
                    try:
                        file.write(extracted_code[0])
                    except:
                        file.write(res)
                scroll_text_on_lcd(re_e, 10, 90, 7, 0.3)
                lcd_rect(0,0,320,290,splash_theme_color,-1)
                draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
                lcd_draw_string(draw,35,28, "RUNNING...", color=(255,0,0), scale=font3, mono_space=False)
                lcd_draw_string(draw,10,90, re_e, color=(255,255,255), scale=font2, mono_space=False)
                display.ShowImage(splash)
                try:
                    os.system('python3 cmd.py')
                except:
                    lcd_rect(0,0,320,290,splash_theme_color,-1)
                    draw.rectangle((20,10,300,80), splash_theme_color, 'white',width=3)
                    lcd_draw_string(draw,10,90, "Can't generate code.", color=(255,255,255), scale=font2, mono_space=False)
                    display.ShowImage(splash)
            
        if quitmark==1:
            print('main quit')
            break

else:
    lcd_draw_string(draw,57,70, "Can't run without network!", color=(255,255,255), scale=font2, mono_space=False)
    lcd_draw_string(draw,57,120, "Press C button to quit.", color=(255,255,255), scale=font2, mono_space=False)
    display.ShowImage(splash)
    while 1:
        if button.press_b():
            break

