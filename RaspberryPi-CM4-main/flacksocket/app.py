import os,sys
import socket
import time
import threading
import cv2 as cv
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw,ImageFont
from flask import Flask , render_template , request ,  Response , redirect
from flask_socketio import SocketIO , send , emit
from xgolib import XGO  
from key import Button
from camera_dog import Dog_Camera

dog=XGO("xgolite")
fm = dog.read_firmware()
splash_theme_color = (15, 21, 46)
color_black=(8,10,26)
color_white=(255,255,255)
# LCD Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
#Draw Methods
def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)
#Load Image
app_image = Image.open("/home/pi/RaspberryPi-CM4-main/pics/app.png") 
unapp_image = Image.open("/home/pi/RaspberryPi-CM4-main/pics/unapp.png")
wifiy = Image.open("/home/pi/RaspberryPi-CM4-main/pics/wifi@2x.jpg")
wifin = Image.open("/home/pi/RaspberryPi-CM4-main/pics/wifi-un@2x.jpg")
font2 = ImageFont.truetype("/home/pi/model/msyh.ttc", 23)
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

exit_event = threading.Event()
button = Button()
def check_button():
    while not exit_event.is_set():
        if button.press_b():
            print("Button B Pressed! Exiting gracefully...")
            dog.reset()
            exit_event.set()
            video_process.terminate()
            os._exit(0)
        time.sleep(0.1)

button_thread = threading.Thread(target=check_button)
button_thread.setDaemon(True)
button_thread.start()


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

#Record Last Access Time
last_access_time = 0

def monitor_connection():
    global last_access_time
    ipadd = ip()
    print(ipadd)
    lcd_rect(0, 180, 320, 240, color=color_black, thickness=-1)
    lcd_draw_string(draw, 100, 200, ipadd, color=color_white, scale=font2)
    
    while not exit_event.is_set():
        current_time = time.time()
        if current_time - last_access_time > 10:
            splash.paste(unapp_image, (0, 0))
            splash.paste(wifiy, (40, 200))
            display.ShowImage(splash)
        else:
            splash.paste(app_image, (0, 0))
            splash.paste(wifiy, (40, 200))
            display.ShowImage(splash)
        time.sleep(2)

    print("Exiting monitor_connection()...")

g_camera = Dog_Camera(debug=False)

def video_handle():
    while not exit_event.is_set():
        success, frame = g_camera.get_frame()
        if not success:
            g_camera.reconnect()
            time.sleep(0.5)
            continue
        #cv.putText(frame, text, (10, 25), cv.FONT_HERSHEY_TRIPLEX, 0.8, (0, 200, 0), 1)
        ret, img_encode = cv.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_encode.tobytes() + b'\r\n')

@app.route('/')
def index():
    global last_access_time
    last_access_time = time.time()
    ip_address = get_ip('wlan0')
    return render_template('demo.html',device_ip = ip_address)
    
@app.route('/camera')
def camera():
    return render_template('camera.html')

@socketio.on('connect')
def on_connect():  
    print('Client connected')
    
@socketio.on('disconnect')
def on_disconnect():  
    print('Client disconnected')
  
@socketio.on('balance')  
def handle_balance(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.imu,int(data))
    
@socketio.on('reset')  
def handle_reset(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.reset)

@socketio.on('action')  
def handle_action(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.perform,int(data))
    
@socketio.on('PushUp')  
def handle_pushup(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))
    
@socketio.on('TakeAPee')  
def handle_takeapee(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))
    
@socketio.on('WaveHand')  
def handle_wavehand(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))

@socketio.on('UpDown')  
def handle_updown(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))

@socketio.on('LookFood')  
def handle_lookfoot(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))

@socketio.on('Dance')  
def handle_dance(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.action,int(data))

@socketio.on('up')  
def handle_up(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.move_x,int(data))

@socketio.on('down')  
def handle_down(data):  
    print(data)
    socketio.start_background_task(dog.move_x,int(data))

@socketio.on('left')  
def handle_left(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.move_y,int(data))

@socketio.on('right')  
def handle_right(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    socketio.start_background_task(dog.move_y,int(data))

@socketio.on('height')  
def handle_height(data):  
    global last_access_time
    last_access_time = time.time()
    print(data)
    y = 'z'
    print(type(data))
    data = int(data)
    print(type(data))
    if data ==50:
        data = 95;
    elif data < 50:
        data = 95-data
    elif data > 50:
        data = 95+data
    print(data)
    socketio.start_background_task(lambda:dog.translation(y,int(data)))

from multiprocessing import Process
def run_video_stream():
    video_app = Flask(__name__)

    @video_app.route('/video_feed')
    def video_feed():
        return Response(video_handle(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @video_app.route('/camera')
    def camera():
        return render_template('camera.html')
    video_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

#Start The Stand-Alone Video Streaming Process
video_process = Process(target=run_video_stream)
video_process.start()

def run_flask():
    socketio.run(app , host='0.0.0.0' , port=80,debug=False,use_reloader=False) 
    
flask_thread = threading.Thread(target=run_flask)
flask_thread.setDaemon(True)
flask_thread.start()

monitor_connection() 
print("App has exited.")
