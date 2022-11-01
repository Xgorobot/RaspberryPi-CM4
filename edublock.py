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
splashb_theme_color = (15,21,46)
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
font2 = ImageFont.truetype("msyh.ttc",22)
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

def main_program():
    display.ShowImage(splash)

#-------------------------init UI---------------------------------
wifiy = Image.open("./pics/wifi@2x.png")
wifin = Image.open("./pics/wifi-un@2x.png")
cn = Image.open("./pics/wifi@2x.png")
uncn = Image.open("./pics/wifi-un@2x.png")


#--------------------------get IP--------------------------
ipadd=ip()
if ipadd=='0.0.0.0':
    print('wlan disconnected')
    draw.bitmap((44,164),wifin)
    lcd_draw_string(draw,80, 160, 'No net!', color=color_white, scale=font2)
else:
    print('wlan connected')
    draw.bitmap((86,164),wifiy)
    lcd_draw_string(draw,110, 160, ipadd, color=color_white, scale=font2)
    

draw.bitmap((65,65),uncn)

display.ShowImage(splash)



import subprocess
import threading

status=0
cmd=b''
order='node /home/pi/Edublocks/server/build/index.js'
pi= subprocess.Popen(order,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
mark=True
running=True
status=0
exitcode=False
def checks():
    global cmd
    for i in iter(pi.stdout.readline,'b'):
        cmd=i
        if cmd!=b'':
            print(cmd)
        if exitcode:
            break
            

t = threading.Thread(target=checks)
t.start()
print('---------------')
while 1:
    if button.press_b():
        exitcode=True
        break
    if cmd[0:6]==b'Launch':
        print('server success')
        draw.bitmap((80,65),uncn)
        display.ShowImage(splash)
    elif cmd[0:12]==b'Successfully':
        print('linked!')
        draw.bitmap((160,65),cn)
        display.ShowImage(splash)

print('aiblocks over')
os.system('sudo fuser -k -n tcp 8081')
print('8081 killed!')
sys.exit()