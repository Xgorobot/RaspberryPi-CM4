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
#-----------------------COMMON INIT-----------------------
import pyzbar.pyzbar as pyzbar

def cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=30):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        "msyh.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

 
# main函数
# openCV 字体
font = cv2.FONT_HERSHEY_SIMPLEX 
#定义图像源
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
if(not cap.isOpened()):
    print("[camera.py:cam]:can't open this camera")

while(True):
    # 读入图片
    ret, img = cap.read() 
    # 转灰度
    img_ROI_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 解码 返回了识别到的多个二维码对象
    barcodes = pyzbar.decode(img_ROI_gray) 
    # 对于每个识别到的二维码区域
    for barcode in barcodes:

        # 条形码数据为字节对象，所以如果我们想在输出图像上
        # 画出来，就需要先将它转换成字符串
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)

        # 打印字符在图片上
        img=cv2AddChineseText(img,text, (10, 30),(0, 255, 0), 30)
        #cv2.putText(img, text , (10,30),font,0.7,(0,255,0),3) 
        # 向终端打印条形码数据和条形码类型
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))

        # 显示
        #cv2.imshow('img_ROI', img_ROI_gray)
        #cv2.imshow('image', img)
    
    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)
    if (cv2.waitKey(1)) == ord('q'):
        break
    if button.press_b():
        break

cap.release()
cv2.destroyAllWindows() 