import cv2
import os,socket,sys,time
import spidev as SPI
import LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import numpy as np

#define colors
btn_selected = (24,47,223)
btn_unselected = (20,30,53)
txt_selected = (255,255,255)
txt_unselected = (76,86,127)
splash_theme_color = (15,21,46)
color_black=(0,0,0)
color_white=(255,255,255)
color_red=(238,55,59)

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
button=Button()

font = ImageFont.truetype("msyh.ttc",22)
font2 = ImageFont.truetype("msyh.ttc",42)

cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)

print("\n [INFO] Initializing face capture. Look the camera and wait ...")
# Initialize individual sampling face count
count = 0
user=1

#draw methods
def lcd_draw_string(splash,x, y, text, color=(255,255,255), font_size=1, scale=1, mono_space=False, auto_wrap=True, background_color=(0,0,0)):
    splash.text((x,y),text,fill =color,font = scale) 

def lcd_rect(x,y,w,h,color,thickness):
    draw.rectangle([(x,y),(w,h)],fill=color,width=thickness)

def main_part():
    lcd_rect(0,0,320,240,color=color_black,thickness=-1)
    lcd_draw_string(draw, 10, 10,'Record', color=color_white, scale=font)
    lcd_draw_string(draw, 250, 10,'Train', color=color_white, scale=font)
    lcd_draw_string(draw, 10, 210,'Quit', color=color_white, scale=font)
    lcd_draw_string(draw, 250, 210,'Recog', color=color_white, scale=font)
    lcd_draw_string(draw, 105, 100,'USER'+str(user), color=color_white, scale=font2)
    display.ShowImage(splash)

main_part()

    
def record():
    global count
    while 1:
        ret, img = cap.read() 
        if ret:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)
            for (x,y,w,h) in faces:
                cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
                count += 1
                print(count)
    
                # Save the captured image into the datasets folder
                cv2.imwrite("dataset/User." + str(user) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
                time.sleep(0.1)
                b,g,r = cv2.split(img)
                img = cv2.merge((r,g,b))
                imgok = Image.fromarray(img)
                display.ShowImage(imgok)
                #cv2.imshow('image', img)
    
                if button.press_b():
                    break
                if count >= 30:
                    print('done')
                    break
        if count>=30:
            break
        if button.press_b():
            break
    #cap.release()
    del faces

    
        
while 1:
    if button.press_c():
        print('a')
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        lcd_draw_string(draw, 30, 90,'FACE TO CAM', color=color_white, scale=font2)
        display.ShowImage(splash)
        record()
        count=0
        user+=1
    if button.press_d():
        print('c')
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        lcd_draw_string(draw, 30, 90,'Training...', color=color_white, scale=font2)
        display.ShowImage(splash)
        os.system('sudo python fr2.py')
        lcd_rect(0,0,320,240,color=color_black,thickness=-1)
        lcd_draw_string(draw, 30, 90,'Done！', color=color_white, scale=font2)
        display.ShowImage(splash)
        print('model train complete')
        time.sleep(2)
    if button.press_b():
        print('c')
        break
    if button.press_a():
        print('d')
        os.system('sudo python fr3.py')
    main_part()


