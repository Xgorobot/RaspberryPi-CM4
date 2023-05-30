import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

import pyzbar.pyzbar as pyzbar

def cv2AddChineseText(img, text, position, textColor=(200, 0, 200), textSize=10):
    if (isinstance(img, np.ndarray)):  
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype("msyh.ttc", textSize, encoding="utf-8")
    draw.text(position, text, textColor, font=fontStyle)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
 
def makefile(s,p):
    t1='''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CN

network={
    ssid="'''
    t2='''
    key_mgmt=WPA-PSK
    }
    '''
    t3='''"
    psk="'''
    files=t1+s+t3+p+'"'+t2
    print(files)
    return files

font = cv2.FONT_HERSHEY_SIMPLEX 
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")

wifi="/etc/wpa_supplicant/wpa_supplicant.conf"

with open(wifi, 'r') as f:
    content=f.read()
    print(content)
    s=content.find('ssid=')
    end=s+6
    while content[end]!='"':
        end+=1
    ssid=content[s+6:end]
    p=content.find('psk=')
    end=p+5
    while content[end]!='"':
        end+=1
    pwd=content[p+5:end]


while(True):
    ret, img = cap.read() 
    img_ROI_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    barcodes = pyzbar.decode(img_ROI_gray) 
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        a = barcodeData.find("S:")
        b = barcodeData.find(";T:")
        zz = barcodeData[a+2:b]
        print(zz)
        c = barcodeData.find("P:")
        d = len(barcodeData)
        yy = barcodeData[c+2:d-9]
        print(yy)
        print("hello")
        ssid = zz
        pwd =yy
        fc=makefile(ssid,pwd)
        with open(wifi, 'w') as f:
            f.write(fc)
        text = "{},{}".format(barcodeData[a+2:b],barcodeData[c+2:d-9])
        img=cv2AddChineseText(img,text, (10, 30),(255, 255, 0), 30)
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
    
    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    
    if button.press_c():
        ssid='XGO2'
        pwd='LuwuDynamics'
        fc=makefile(ssid,pwd)
        with open(wifi, 'w') as f:
            f.write(fc)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break

cap.release()
cv2.destroyAllWindows() 
