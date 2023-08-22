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
【角色】请扮演一个资深的机器人开发者，你精通树莓派，机器人和python开发。
【任务】根据命令词让机器狗按照提供的python库自动生成python代码。
【要求】只返回根据命令词语自动生成的python代码，代码前面的内容和代码后面的内容都不要回复给我。
具体的python库如下，机器狗的Python控制接口,分别为前进，后退、左平移、右平移，旋转、沿XYZ轴三个轴方向平移和旋转，以及做动作组。
xgo.move_x(step)  #step的单位为毫米,前进为正,后退为负，0表示停止，取值范围是[-25,25]mm。
xgo.move_y(step)  #step的单位为毫米,左平移为正,右平移为负，0表示停止，取值范围是[-18,18]mm。
xgo.turn(speed)  #speed为角速度, 正数为顺时针,负数为逆时针，0表示停止，取值范围是[-150,150] 。
xgo.pace(mode) #mode为slow,normal或者high 。表示机器狗的踏步频率高低。
time.sleep(X) #X的单位是秒，表示上一条指令运动时长。
xgo.action(id) #id为动作组接口，id取值范围为1-21,分别对应[趴下,站起,转圈,匍匐前进,原地踏步,蹲起,沿x转动,沿y转动,沿z转动,三轴转动,撒尿,坐下,招手,伸懒腰,波浪运动,摇摆运动,求食,找食物,握手,展示机械臂,俯卧撑],即趴下的id为1,匍匐前进为4,求食为18。        
xgo.translation(direction, data)  # direction取值为'x','y','z' ,data的单位是毫米，沿X轴正方向平移为正数，0表示回到初始位置，沿着X负方向平移为负数，取值范围是[-35,35]mm，y轴和z轴同理。
xgo.attitude(direction, data)  #direction取值为'r','p','y' ,data的单位是度，沿X轴正时针旋转为正数，0表示回到初始位置，沿着X逆时针旋转为负数，取值范围是[-20,20]mm，y轴和z轴旋转运动同理。
arm( arm_x, arm_z) #表示arm_x取值范围是[-80,155]和arm_z的取值范围是[-95，155]
claw(pos) #pos的取值是0-255，其中0表示机夹爪完全张开，255表示夹爪完全闭合。
imu(mode) #mode的取值为0或者1，0代表关闭自稳定模式，1表示打开自稳定模式。
reset()# 复位
lcd_picture(filename)   #此函数用于机器狗显示表情，有攻击，愤怒，厌恶，喜欢，调皮，祈祷，伤心，敏感，困，道歉，惊讶。
我希望你能根据我的命令,利用以上函数写出对应的运动代码。

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
xgo=XGO("xgolite")
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)

示例2
命令:左平移5秒
代码:
import time
from xgolib import XGO
xgo=XGO("xgolite")
xgo.move_y(15)
time.sleep(5)
xgo.move_y(0)

示例3
命令:以100的角速度旋转3秒
代码:
import time
from xgolib import XGO
xgo=XGO("xgolite")
xgo.turn(100)
time.sleep(3)
xgo.turn(0)


示例4
命令:前进3秒,撒个尿,左转3秒,展示机械臂:
import time
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

示例5
命令：显示开心的表情，并伸懒腰
import time
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO("xgolite")
XGO_edu = XGOEDU()
xgo.action(14)
time.sleep(3)
XGO_edu.lcd_picture(like) 
示例结束了，请根据命令返回python代码，把注释写在返回的代码里面，最后一句是xgo.reset()让其复位，你必须输出md格式的文档。
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

