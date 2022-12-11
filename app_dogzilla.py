import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button

path=os.getcwd()

#define colors
splash_theme_color = (15,21,46)
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splashb_theme_color = (8,10,26)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)
#display init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
#button
button=Button()
#const
firmware_info='v1.0'
#font
font1 = ImageFont.truetype("msyh.ttc",15)
font2 = ImageFont.truetype("msyh.ttc",23)
font3 = ImageFont.truetype("msyh.ttc",30)
#init splash
splash = Image.new("RGB", (display.height, display.width ),splash_theme_color)
draw = ImageDraw.Draw(splash)
#splash=splash.rotate(180)
display.ShowImage(splash)

def get_ip(ifname):
    import socket,struct,fcntl
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', bytes(ifname[:15],'utf-8')))[20:24])

def ip():
    try:
        ipchr=get_ip('wlan0')
    except:
        ipchr='0.0.0.0'
    return ipchr

#draw methods
def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)


#-------------------------init UI---------------------------------
wifiy = Image.open("./pics/wifi@2x.jpg")
wifin = Image.open("./pics/wifi-un@2x.jpg")
cn = Image.open("./pics/app.png")
uncn = Image.open("./pics/unapp.png")
lcd_rect(0,195,320,240,(48,50,73),thickness=-1)


#--------------------------get IP&SSID--------------------------
ipadd=ip()
if ipadd=='0.0.0.0':
    print('wlan disconnected')
    lcd_rect(0,195,320,240,(48,50,73),thickness=-1)
    splash.paste(wifin,(65,200))
    lcd_draw_string(draw,100, 200, 'No net!', color=color_white, scale=font2)
else:
    print('wlan connected')
    lcd_rect(0,195,320,240,(48,50,73),thickness=-1)
    splash.paste(wifiy,(65,200))
    lcd_draw_string(draw,100, 200, ipadd, color=color_white, scale=font2)
    

splash.paste(uncn,(0,0))
display.ShowImage(splash)
# Version: V1.2.3
from flask import Flask, render_template, Response
import socket
import os
import time
import threading
import cv2 as cv
import sys
import struct
import inspect
import ctypes

from DOGZILLALib import DOGZILLA

from camera_dogzilla import Dogzilla_Camera
#from joystick_dogzilla import Dogzilla_Joystick
#from oled_dogzilla import Dogzilla_OLED

from gevent import pywsgi


g_debug = False
if len(sys.argv) > 1:
    if str(sys.argv[1]) == "debug":
        g_debug = True
print("debug=", g_debug)


# 底层处理库
g_dog = DOGZILLA()


# 摄像头库
g_camera = Dogzilla_Camera(debug=g_debug)
#g_oled = Dogzilla_OLED(g_dog, debug=g_debug)

g_tcp_ip = "x.x.x.x"

g_init = False
g_mode = 'Home'


app = Flask(__name__)


# 速度控制
g_step_control = 50
g_pace_freq = 2
g_motor_speed = [0, 0, 0, 0]
g_car_stabilize_state = 0

# STEP width缩放比例
STEP_SCALE_X = 0.25
STEP_SCALE_Y = 0.2
STEP_SCALE_Z = 0.7

g_height = 108
g_shoulder = 0
g_action_continuous = 0
g_press_up = 0

g_motor_id = 1

# TCP未接收命令超时计数
g_tcp_except_count = 0

def my_map(x, in_min, in_max, out_min, out_max):
    return (out_max - out_min) * (x - in_min) / (in_max - in_min) + out_min



# 将十六进制字符串转化成整型数。
# str_hex只支持两位字符串（一个字节数据）。
# HEX=True表示返回无符号整型, HEX=False表示返回带符号整型。
def hex2int(str_hex, HEX=True):
    num_hex = int(str_hex, 16)
    if HEX:
        return num_hex
    if num_hex > 127:
        num_hex = num_hex - 256
    return num_hex

# 将整型十进制数转化成十六进制数。
# int_hex=[-128, 255]
def int2hex(int_hex):
    if int_hex < -128 or int_hex > 255:
        int_hex = 0
    if int_hex < 0:
        int_hex = int_hex + 256
    return int_hex

# 获取IP地址
def get_ip_address():
    ip = os.popen(
        "/sbin/ifconfig eth0 | grep 'inet' | awk '{print $2}'").read()
    ip = ip[0: ip.find('\n')]
    if(ip == '' or len(ip) > 15):
        ip = os.popen(
            "/sbin/ifconfig wlan0 | grep 'inet' | awk '{print $2}'").read()
        ip = ip[0: ip.find('\n')]
        if(ip == ''):
            ip = 'x.x.x.x'
    if len(ip) > 15:
        ip = 'x.x.x.x'
    return ip

# 恢复初始位置
def dogzilla_reset():
    global g_height, g_shoulder, g_action_continuous
    global g_press_up, g_pace_freq
    g_height = 108
    g_shoulder = 0
    g_action_continuous = 0
    g_press_up = 0
    g_pace_freq = 2
    g_dog.action(0xff)

# 单腿控制恢复初始位置
def dogzilla_leg_reset():
    g_dog.leg(1, [0, 0, 108])
    time.sleep(.005)
    g_dog.leg(2, [0, 0, 108])
    time.sleep(.005)
    g_dog.leg(3, [0, 0, 108])
    time.sleep(.005)
    g_dog.leg(4, [0, 0, 108])


# 返回电池电压
def return_battery_voltage():
    global g_socket
    T_TYPE = 0x01
    T_FUNC = 0x02
    T_LEN = 0x06
    vol = int(g_dog.read_battery())
    reserve = 0x00
    checknum = (T_TYPE + T_FUNC + T_LEN + vol + reserve) % 256
    data = "$%02x%02x%02x%02x%02x%02x#" % (T_TYPE, T_FUNC, T_LEN, vol, reserve, checknum)
    g_socket.send(data.encode(encoding="utf-8"))
    if g_debug:
        print("voltage:", vol)
        print("tcp send:", data)


# 返回遥控界面数据
def return_ctrl_data():
    global g_socket
    T_TYPE = 0x01
    T_FUNC = 0x10
    T_LEN = 0x08
    step = g_step_control
    freq = g_pace_freq
    stab = g_car_stabilize_state
    height = g_height
    checknum = (T_TYPE + T_FUNC + T_LEN + step + freq + stab + height) % 256
    data = "$%02x%02x%02x%02x%02x%02x%02x%02x#" % (T_TYPE, T_FUNC, T_LEN, step, freq, stab, height, checknum)
    g_socket.send(data.encode(encoding="utf-8"))
    if g_debug:
        print("step:%d, freq:%d, stab:%d, height:%d" % (step, freq, stab, height))
        print("ctrl send:", data)


# 返回全屏界面数据
def return_posture_data():
    global g_socket
    T_TYPE = 0x01
    T_FUNC = 0x20
    T_LEN = 0x06
    height = g_height
    shoulder = int2hex(g_shoulder)
    checknum = (T_TYPE + T_FUNC + T_LEN + height + shoulder) % 256
    data = "$%02x%02x%02x%02x%02x%02x#" % (T_TYPE, T_FUNC, T_LEN, height, shoulder, checknum)
    g_socket.send(data.encode(encoding="utf-8"))
    if g_debug:
        print("posture send:", data)


# 返回动作组界面数据
def return_action_data():
    global g_socket
    T_TYPE = 0x01
    T_FUNC = 0x30
    T_LEN = 0x06
    continuous = g_action_continuous
    reserve = 0x00
    checknum = (T_TYPE + T_FUNC + T_LEN + continuous + reserve) % 256
    data = "$%02x%02x%02x%02x%02x%02x#" % (T_TYPE, T_FUNC, T_LEN, continuous, reserve, checknum)
    g_socket.send(data.encode(encoding="utf-8"))
    if g_debug:
        print("action send:", data)


# 返回舵机控制界面数据
def return_motor_data():
    global g_socket
    T_TYPE = 0x01
    T_FUNC = 0x40
    T_LEN = 0x1A
    angle_float = g_dog.read_motor()
    angle_int = []
    angle_sum = 0
    for i in range(len(angle_float)):
        temp = int(angle_float[i])
        angle_int.append(temp)
        angle_sum = angle_sum + temp
    checknum = (T_TYPE + T_FUNC + T_LEN + angle_sum) % 256
    data = "$%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x#" % \
        (T_TYPE, T_FUNC, T_LEN, 
        int2hex(angle_int[0]), int2hex(angle_int[1]), int2hex(angle_int[2]), 
        int2hex(angle_int[3]), int2hex(angle_int[4]), int2hex(angle_int[5]), 
        int2hex(angle_int[6]), int2hex(angle_int[7]), int2hex(angle_int[8]), 
        int2hex(angle_int[9]), int2hex(angle_int[10]), int2hex(angle_int[11]), checknum)
    g_socket.send(data.encode(encoding="utf-8"))
    if g_debug:
        print("motor", angle_int)
        print("action send:", data)

# 动作组-俯卧撑控制线程
def task_press_up_handle():
    global g_press_up
    state_count = 0
    index = 0
    while True:
        if g_press_up:
            if state_count == 1:
                g_dog.translation('z', 75)
            elif state_count == 5:
                g_dog.translation('z', 100)
            elif state_count == 10:
                state_count = 0
                index = index + 1
            state_count = state_count + 1
            if index > 5:
                g_press_up = 0
                state_count  = 0
                index = 0
                g_dog.action(0xff)
        else:
            if state_count > 0:
                state_count  = 0
                index = 0
        time.sleep(.15)

# USB无线手柄
# def task_joystick_handle():
#     js = Dogzilla_Joystick(g_dog, debug=g_debug)
#     # if not js.is_Opened():
#     #     return
#     while True:
#         state = js.joystick_handle()
#         if state != js.STATE_OK:
#             if state == js.STATE_KEY_BREAK:
#                 break
#             time.sleep(1)
#             js.reconnect()

# OLED刷新任务
# def task_oled_handle():
#     global g_oled
#     if g_debug:
#         print("Start OLED Task")
#     while True:
#         g_oled.main_program()
#         time.sleep(1)




# 协议解析部分
def parse_data(data):
    # print(data)
    global g_mode
    global g_motor_speed
    global g_step_control, g_pace_freq
    global g_car_stabilize_state
    global g_height, g_action_continuous, g_shoulder
    global g_press_up
    data_size = len(data)
    # 长度校验
    if data_size < 8:
        if g_debug:
            print("The data length is too short!", data_size)
        return

    if hex2int(data[5:7]) != data_size-8:
        if g_debug:
            print("The data length error!", hex2int(data[5:7]), data_size-8)
        return
    # 和校验
    checknum = 0
    num_checknum = hex2int(data[data_size-3:data_size-1])
    for i in range(0, data_size-4, 2):
        checknum = (hex2int(data[1+i:3+i]) + checknum) % 256
        # print("check:", i, hex2int(data[1+i:3+i]), checknum)
    if checknum != num_checknum:
        if g_debug:
            print("num_checknum error!", checknum, num_checknum)
            print("checksum error! cmd:0x%02x, calnum:%d, recvnum:%d" % (hex2int(data[3:5]), checknum, num_checknum))
        return
    
    
    # 解析命令标记
    cmd = data[3:5]
    if cmd == "0F":  # 回到主界面
        func = hex2int(data[7:9])
        if g_debug:
            print("cmd func=", func)
        g_mode = 'Home'
        if func == 0:
            return_battery_voltage()
            dogzilla_reset()
        elif func == 1:
            return_ctrl_data()
            g_mode = 'Standard'
        elif func == 2:
            return_posture_data()
            g_mode = 'Fullscreen'
        elif func == 3:
            return_action_data()
        elif func == 4:
            return_motor_data()
        elif func == 5:
            dogzilla_leg_reset()

    elif cmd == "02":  # 获取电池电压
        if g_debug:
            print("get voltage")
        return_battery_voltage()

    elif cmd == "10":  # 获取控制页面信息
        if g_debug:
            print("get ctrl page info")

    # 摇杆控制
    elif cmd == "11":
        num_x = hex2int(data[7:9], False)
        num_y = hex2int(data[9:11], False)
        speed_x = int(num_y / 100.0 * STEP_SCALE_X * g_step_control)
        speed_y = int(-num_x  / 100.0 * STEP_SCALE_Y * g_step_control)
        if g_debug:
            print("speed_x:%.2f, speed_y:%.2f" % (speed_x, speed_y))
        g_dog.move_x(speed_x)
        g_dog.move_y(speed_y)

    # 按键控制
    elif cmd == "12":
        num_dir = hex2int(data[7:9])
        if g_debug:
            print("btn ctl:%d" % num_dir)
        if num_dir == 1:
            step = int(STEP_SCALE_X * g_step_control)
            g_dog.forward(step)
        elif num_dir == 2:
            step = int(STEP_SCALE_X * g_step_control)
            g_dog.back(step)
        elif num_dir == 3:
            step = int(STEP_SCALE_Y * g_step_control)
            g_dog.left(step)
        elif num_dir == 4:
            step = int(STEP_SCALE_Y * g_step_control)
            g_dog.right(step)
        elif num_dir == 5:
            # step = int(STEP_SCALE_Z * g_step_control)
            step = int(my_map(g_step_control, 0, 100, 20, STEP_SCALE_Z*100))
            g_dog.turnleft(step)
        elif num_dir == 6:
            # step = int(STEP_SCALE_Z * g_step_control)
            step = int(my_map(g_step_control, 0, 100, 20, STEP_SCALE_Z*100))
            g_dog.turnright(step)
        elif num_dir == 7:
            dogzilla_reset()
        elif num_dir == 0:
            g_dog.stop()


    # 控制步伐宽度控制
    elif cmd == '13':
        num_width = hex2int(data[7:9])
        if g_debug:
            print("step width:%d" % num_width)
        g_step_control = num_width
        if g_step_control > 100:
            g_step_control = 100
        if g_step_control < 20:
            g_step_control = 20
    
    # 控制频率
    elif cmd == '14':
        num_freq = hex2int(data[7:9])
        if g_debug:
            print("pace freq:%d" % num_freq)
        if 0 < num_freq < 4:
            g_pace_freq = num_freq
            if g_pace_freq == 1:
                g_dog.pace("slow")
            elif g_pace_freq == 2:
                g_dog.pace("normal")
            elif g_pace_freq == 3:
                g_dog.pace("high")


    # 自稳开关
    elif cmd == '15':
        num_stab = hex2int(data[7:9])
        if g_debug:
            print("car stabilize:%d" % num_stab)
        if num_stab > 0:
            g_car_stabilize_state = 1
        else:
            g_car_stabilize_state = 0
        g_dog.imu(g_car_stabilize_state)

    # 获取姿态页面数据
    elif cmd == '20':
        if g_debug:
            print("get attitude info")

    # 控制身体姿态
    elif cmd == "21":
        num_x = hex2int(data[7:9], False)
        num_y = hex2int(data[9:11], False)
        pose_x = int(num_x / 5)
        pose_y = -int(num_y / 6.6)
        g_dog.attitude(['r','p'],[pose_x,pose_y])
        if g_debug:
            print("pose_x:%d, pose_y:%d" % (pose_x, pose_y))

    # 控制身体高低
    elif cmd == '22':
        num_height = hex2int(data[7:9])
        if g_debug:
            print("height:%d" % num_height)
        # 身高限制[75, 115]
        if 75 < num_height < 115:
            g_height = num_height
            g_dog.translation('z', g_height)
    
    # 控制肩膀
    elif cmd == '23':
        num_shoulder = hex2int(data[7:9], False)
        if g_debug:
            print("shoulder:%d" % num_shoulder)
        # 限制[-11, 11]
        if -11 < num_shoulder < 11:
            g_shoulder = num_shoulder
            g_dog.attitude('y', g_shoulder)

    # 控制动作组
    elif cmd == '31':
        num_action = hex2int(data[7:9])
        if g_debug:
            print("action:%d" % num_action)
        if num_action == 0:
            dogzilla_reset()
        elif num_action == 20:
            g_press_up = 1
        else:
            g_press_up = 0
            g_dog.action(num_action)

    # 动作组轮播
    elif cmd == '32':
        num_continuous = hex2int(data[7:9])
        if g_debug:
            print("continuous:%d" % num_continuous)
        if num_continuous == 1:
            g_action_continuous = num_continuous
            g_dog.perform(g_action_continuous)
        elif num_continuous == 0:
            g_action_continuous = num_continuous
            g_dog.perform(g_action_continuous)

    # 初始位置
    elif cmd == '33':
        num_reset = hex2int(data[7:9])
        if g_debug:
            print("reset:%d" % num_reset)
        if num_reset == 1:
            dogzilla_leg_reset()
        elif num_reset == 2:
            dogzilla_reset()


    # 单舵机控制
    elif cmd == '41':
        num_motor = hex2int(data[7:9])
        num_parm_3 = hex2int(data[9:11], False)
        num_parm_2 = hex2int(data[11:13], False)
        num_parm_1 = hex2int(data[13:15], False)
        if g_debug:
            print("motor:", num_motor, num_parm_1, num_parm_2, num_parm_3)
        if 0 < num_motor < 5: 
            motorid = [num_motor*10+1, num_motor*10+2, num_motor*10+3]
            value = [num_parm_1, num_parm_2, num_parm_3]
            g_dog.motor(motorid, value)

    # 单腿控制
    elif cmd == '51':
        num_leg = hex2int(data[7:9])
        num_parm_1 = hex2int(data[9:11], False)
        num_parm_2 = hex2int(data[11:13], False)
        num_parm_3 = hex2int(data[13:15], False)
        if g_debug:
            print("leg:", num_leg, num_parm_1, num_parm_2, num_parm_3)
        if 0 < num_leg < 5: 
            value = [num_parm_1, num_parm_2, num_parm_3]
            g_dog.leg(num_leg, value)

    # 重新标定舵机，谨慎使用。
    elif cmd == 'AA':
        num_state = hex2int(data[7:9]) #1为标定，0为完成标定
        num_verify = hex2int(data[9:11])
        if num_verify == 0x55:
            g_dog.calibration(num_state)
    else:
        pass


# socket TCP通信建立
def start_tcp_server(ip, port):
    global g_init, g_tcp_except_count
    global g_socket, g_mode
    g_init = True
    if g_debug:
        print('start_tcp_server')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(None)
    sock.bind((ip, port))
    sock.listen(1)

    while True:
        print("Waiting for the client to connect!")
        tcp_state = 0
        times = 0
        g_tcp_except_count = 0
        g_socket, address = sock.accept()
        splash.paste(cn,(0,0))
        display.ShowImage(splash)
        print("Connected, Client IP:", address)
        tcp_state = 1
        while True:
            try:
                if times == 0:
                    # 首次连接报电池电量
                    return_battery_voltage()
                    times = 1
                tcp_state = 2
                cmd = g_socket.recv(1024).decode(encoding="utf-8")
                print(cmd)
                if not cmd:
                    break
                tcp_state = 3
                if g_debug:
                    print("   [-]cmd:{0}, len:{1}".format(cmd, len(cmd)))
                tcp_state = 4
                index1 = cmd.rfind("$")
                index2 = cmd.rfind("#")
                if index1 < 0 or index2 <= index1:
                    continue
                tcp_state = 5
                parse_data(cmd[index1:index2 + 1])
                g_tcp_except_count = 0
            except:
                if tcp_state == 2:
                    g_tcp_except_count += 1
                    if g_tcp_except_count >= 10:
                        g_tcp_except_count = 0
                        break
                else:
                    if g_debug:
                        print("!!!----TCP Except:%d-----!!!" % tcp_state)
                continue
            # parse_data(cmd[index1:index2 + 1])
        print("socket disconnected!")
        splash.paste(uncn,(0,0))
        display.ShowImage(splash)
        g_socket.close()
        g_mode = 'Home'


# 初始化TCP Socket
def init_tcp_socket():
    global g_tcp_ip
    if g_init:
        return
    while True:
        if button.press_b():
            break
        ip = get_ip_address()
        if ip == "x.x.x.x":
            g_tcp_ip = ip
            print("get ip address fail!")
            time.sleep(.5)
            
            continue
        if ip != "x.x.x.x":
            g_tcp_ip = ip
            print("TCP Service IP=", ip)
            break
    task_tcp = threading.Thread(target=start_tcp_server, name="task_tcp", args=(ip, 6000))
    task_tcp.setDaemon(True)
    task_tcp.start()
    if g_debug:
        print('-------------------Init TCP Socket!-------------------------')



# 根据状态机来运行程序包含视频流返回
def mode_handle():
    global g_mode, g_camera
    if g_debug:
        print("----------------------------mode_handle--------------------------")
    while True:
        m_fps = 0
        t_start = time.time()
        while True:
            if g_mode == 'Standard' or g_mode == 'Fullscreen':
                success, frame = g_camera.get_frame()
                m_fps = m_fps + 1
                fps = m_fps / (time.time() - t_start)
                text = "FPS:" + str(int(fps))
                if not success:
                    m_fps = 0
                    t_start = time.time()
                    if g_debug:
                        print("-----The camera is reconnecting...")
                    g_camera.reconnect()
                    time.sleep(.5)
                    continue
                cv.putText(frame, text, (10, 25), cv.FONT_HERSHEY_TRIPLEX, 0.8, (0, 200, 0), 1)
                ret, img_encode = cv.imencode('.jpg', frame)
                if ret:
                    img_encode = img_encode.tobytes()
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + img_encode + b'\r\n')
            else:
                time.sleep(.1)
                m_fps = 0
                t_start = time.time()



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    if g_debug:
        print("----------------------------video_feed--------------------------")
    return Response(mode_handle(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/init')
def init():
    init_tcp_socket()
    return render_template('init.html')



task_1 = threading.Thread(target=task_press_up_handle, name="task_press_up")
task_1.setDaemon(True)
task_1.start()

def check_button():
    while 1:
        time.sleep(0.1)
        if button.press_b():
            break
    print('try to kill')
    os.system('sudo fuser -k -n tcp 6500')
    print('6500 killed!')

task_2=threading.Thread(target=check_button, name="task_press_up")
task_2.start()


init_tcp_socket()

#g_dog.action(14) # 开机展示伸懒腰动作
print("Waiting for connect to the APP!")

while 1:
    if button.press_b():
        break
    try:
        server = pywsgi.WSGIServer(('0.0.0.0', 6500), app)
        server.serve_forever()
    except KeyboardInterrupt:
        #g_oled.clear(True)
        del g_dog
        print("-----program end-----")

print('app quit!')
