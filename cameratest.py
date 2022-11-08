import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont

display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

splash = Image.new("RGB", (display.height, display.width ),"black")
draw = ImageDraw.Draw(splash)

count=0

def main():
    global count
    cap=cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)

    while cap.isOpened():
        ret,img=cap.read()
        imgok = Image.fromarray(img)
        display.ShowImage(imgok)


main()