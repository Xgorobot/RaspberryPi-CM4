# -*- coding: utf-8 -*-
'''
readme
xgo抓取小球demo,按键控制介绍，程序运行之后按左下键会退出程序，按右下键会进入调试模式，左上键进入抓取模式。每次进入调试模式会更改需要抓取球的颜色
如何调整可通过屏幕看到
每次抓取结束后会自动终止程序
尽量选择光照充足的地方运行
'''
import os,threading
import numpy as np
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
from xgolib import XGO
import cv2
from subprocess import Popen
from uiutils import dog, draw, display, Button,language
import sys, time

# IniT Key
button = Button()

import xgoscreen.LCD_2inch as LCD_2inch

display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()
splash_theme_color = (15, 21, 46)
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

font = cv2.FONT_HERSHEY_SIMPLEX
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
print("摄像头初始化完毕")
fm = dog.read_firmware()
if fm[0] == 'M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0', version="xgomini")
    dog_type = 'M'
else:
    print('XGO-LITE')
    dog = XGO(port='/dev/ttyAMA0', version="xgolite")
    dog_type = 'L'
CircleCount = 0
UnCircleCount = 0
mx = 0
my = 0
mr = 0
distance = 0
yaw_err = 0
if dog_type == 'L':
    mintime_yaw = 0.8
    mintime_x = 0.1
    x_speed_far = 16
    x_speed_slow = 8
    turn_speed = 8
else:
    mintime_yaw = 0.7
    mintime_x = 0.3
    x_speed_far = 16
    x_speed_slow = 8
    turn_speed = 8
mode = 0


# 机械臂抓取
def catch_arm(dog):
    dog.translation('z', 10)
    dog.attitude('p', 15)
    dog.claw(5)
    time.sleep(1)
    dog.arm_polar(200, 130)
    time.sleep(2)
    dog.claw(245)
    time.sleep(1)
    dog.arm_polar(90, 100)

def down_arm(dog):
    dog.translation('z', 10)
    dog.attitude('p', 15)
    time.sleep(1)
    dog.arm_polar(200, 130)
    time.sleep(2)
    dog.claw(15)
    time.sleep(1)
    dog.arm_polar(90, 100)


# 文字可视化操作提示
def lcd_draw_string(
        splash,
        x,
        y,
        text,
        color=(255, 255, 255),
        font_size=16,
        max_width=220,
        max_lines=5,
        clear_area=True
):
    font = ImageFont.truetype("/home/jinliang/model/msyh.ttc", font_size)

    line_height = font_size + 2
    total_height = max_lines * line_height

    if clear_area:
        draw.rectangle((x, y, x + max_width, y + total_height), fill=(15, 21, 46))
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    if max_lines:
        lines = lines[:max_lines]

    for i, line in enumerate(lines):
        splash.text((x, y + i * line_height), line, fill=color, font=font)


# 修改颜色
def change_color():
    global mode
    if mode == 3:
        mode = 1
    else:
        mode += 1
    if mode == 1:  # red
        a = 'red'
        return a
    elif mode == 2:  # green
        a = 'green'
        return a
    elif mode == 3:  # blue
        a = 'blue'
        return a


def Image_Processing(dog, a, mintime_yaw, mintime_x, cap, xdistance=22, x_center=160):
    global CircleCount, mx, my, mr, distance, yaw_err, UnCircleCount
    turn_time = mintime_yaw
    run_time = mintime_x
    ret, image = cap.read()
    image_copy = image
    if image is None:
        exit()
    x, y, r = 0, 0, 0
    image = cv2.GaussianBlur(image, (3, 3), 0)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    def color_recognize(a: str):
        if a == "blue":
            lower_blue = np.array([90, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            return mask
        elif a == "green":
            lower_green = np.array([40, 60, 75])
            upper_green = np.array([77, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            return mask
        elif a == "red":
            lower_red1 = np.array([0, 100, 80])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 80])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)
            return mask

    mask = color_recognize(a)
    masked_image = cv2.bitwise_and(image, image, mask=mask)
    image = masked_image
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 30, param1=36, param2=18, minRadius=8, maxRadius=45)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        # 找出半径最大的圆
        max_radius_index = np.argmax(circles[:, 2])
        max_radius_circle = circles[max_radius_index]
        x, y, r = max_radius_circle
        CircleCount += 1
        mx = (CircleCount - 1) * mx / CircleCount + x / CircleCount
        my = (CircleCount - 1) * my / CircleCount + y / CircleCount
        mr = (CircleCount - 1) * mr / CircleCount + r / CircleCount

        # 绘制半径最大的圆的轮廓
        cv2.circle(image_copy, (x, y), r, (0, 255, 0), 2)
        # 绘制圆心
        cv2.circle(image_copy, (x, y), 2, (0, 0, 255), 3)

        #显示绘制了圆的图像
        b, g, r1 = cv2.split(image_copy)
        image_copy = cv2.merge((r1, g, b))
        imgok = Image.fromarray(image_copy)
        display.ShowImage(imgok)

        if len(circles[0]) == 1:
            ball = circles[0][0]
            x, y, r = int(ball[0]), int(ball[1]), int(ball[2])
            cv2.circle(image, (x, y), r, (0, 0, 255), 2)
            cv2.circle(image, (x, y), 2, (0, 0, 255), 2)
            print("x:{}, y:{}, r:{}".format(x, y, r))
            CircleCount += 1
            mx = (CircleCount - 1) * mx / CircleCount + x / CircleCount
            my = (CircleCount - 1) * my / CircleCount + y / CircleCount
            mr = (CircleCount - 1) * mr / CircleCount + r / CircleCount
    else:
        UnCircleCount += 1

    if UnCircleCount >= 15:
        UnCircleCount = 0
        print('没看见球，可能走过了，后退一点重新找球')
        dog.move_x(-10)
        time.sleep(0.8)
        dog.stop()
        time.sleep(0.2)
        return 1

    if CircleCount >= 15:
        CircleCount = 0
        distance = 54.82 - mr
        x_center = x_center
        yaw_err = -(mx - x_center) / distance
        if dog_type == 'L':
            if abs(mx - x_center) > 25:
                turn_time = min(abs(0.4 * yaw_err) / 8 + mintime_yaw, 2)
            if distance >= 30:
                run_time = distance / 40 + mintime_x
                turn_time = abs(9 * yaw_err) / 8 + mintime_yaw
            elif 25 <= distance < 30:
                run_time = distance / 75 + mintime_x
                turn_time = abs(5 * yaw_err) / 8 + mintime_yaw
            else:
                run_time = mintime_x + 0.3

        else:
            if abs(mx - x_center) > 25:
                turn_time = min(abs(0.4 * yaw_err) / 8 + mintime_yaw, 2)
            if distance >= 30:
                run_time = distance / 50 + mintime_x
                turn_time = abs(9 * yaw_err) / 8 + mintime_yaw
            elif 25 <= distance < 30:
                run_time = distance / 80 + mintime_x
                turn_time = abs(5 * yaw_err) / 8 + mintime_yaw
            else:
                run_time = mintime_x + 0.2

        x_distance = xdistance  # 如果夹球时距离远，需要减小x_distance
        y_1 = 20
        y_2 = 25
        if distance < x_distance and -y_1 / distance <= yaw_err <= y_1 / distance:  # distance控制距离球的前后，yaw_err控制球的左右，需要根据每台xgo，具体微调一下抓球的位置
            print("满足条件一抓取")
            dog.attitude('y', 5 * yaw_err)
            dog.translation('x', (distance - 20))
            time.sleep(0.5)
            catch_arm(dog)
            time.sleep(2)
            return 0

        if distance < x_distance and -y_2 <= mx - x_center <= y_2:  # distance控制距离球的前后，mx-160控制球的左右，需要根据每台xgo，具体微调一下抓球的位置
            print("满足条件二抓取")
            dog.attitude('y', 0.25 * (x_center - mx))
            dog.translation('x', (distance - 20))
            time.sleep(0.5)
            catch_arm(dog)
            time.sleep(2)
            return 0
        if distance >= x_distance + 3:
            print("距离还远，快速前进")
            dog.gait_type('trot')
            dog.move_x(x_speed_far)
            time.sleep(run_time)
            dog.move_x(0)
            time.sleep(0.2)
        elif x_distance - 3 <= distance <= x_distance + 3:
            print("距离不远了，可以微调")
            dog.gait_type("slow_trot")
            dog.move_x(x_speed_slow)
            time.sleep(run_time)
            dog.move_x(0)
            time.sleep(0.1)
        if yaw_err > y_1 / distance:
            print("左转")
            dog.gait_type("slow_trot")
            dog.turn(turn_speed)
            time.sleep(turn_time)
            dog.turn(0)
            time.sleep(0.1)
        elif yaw_err < -y_1 / distance:
            print("右转")
            dog.gait_type("slow_trot")
            dog.turn(-turn_speed)
            time.sleep(turn_time)
            dog.turn(0)
            time.sleep(0.1)
    return 1


# 保存和读取
def save_variable_value(value, file_path='variable_value.txt'):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str(value))
        print(f"已保存变量值 {value} 到 {file_path}")
    except Exception as e:
        print(f"保存变量值时出错: {e}")

def load_variable_value(default, file_path='variable_value.txt'):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                value = file.read().strip()
                if value:
                    try:
                        # 尝试转换为浮点数
                        return float(value)
                    except ValueError:
                        # 如果转换失败，返回默认值
                        return default
    except Exception as e:
        print(f"读取变量值时出错: {e}")
    return default
    
# Set language (cn for Chinese, other for English)
la=language()
# Language texts for display only
display_texts = {
    'cn': {
        'exit': "左下角键:退出程序",
        'change_color': "右上角键:改颜色({})", 
        'debug': "右下角键:调试模式",
        'catch': "左上角键:抓取模式",
        'debug_title': "调试模式 颜色: {}",
        'current_dist': "当前距离: {:.1f}",
        'decrease': "左上角键:减小距离",
        'increase': "右上角键:增大距离", 
        'save': "右下角键:保存设置",
        'exit_debug': "左下角键:退出调试",
        'saved': "保存成功!"
    },
    'en': {
        'exit': "BL: Exit",
        'change_color': "TR: Color({})", 
        'debug': "BR: Debug",
        'catch': "TL: Catch",
        'debug_title': "Debug Color: {}",
        'current_dist': "Dist: {:.1f}",
        'decrease': "TL: Dec dist",
        'increase': "TR: Inc dist", 
        'save': "BR: Save",
        'exit_debug': "BL: Exit debug",
        'saved': "Saved!"
    }
}

dog.attitude('p', 15)
dog.translation('z', 75)
time.sleep(3)
color = "red"
mode = 1  # 初始化mode变量

while True:
    x_distance = load_variable_value(default=22.0, file_path='x_distance.txt')
    x_center = load_variable_value(default=160.0, file_path='x_center.txt')
    
    # 主界面显示
    splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
    draw = ImageDraw.Draw(splash)
    draw.rectangle([0, 0, display.width, display.height], fill=(15, 21, 46))
    
    # 定义要显示的行内容和初始y坐标
    menu_items = [
        display_texts[la]['exit'],
        display_texts[la]['change_color'].format(color), 
        display_texts[la]['debug'],
        display_texts[la]['catch']
    ]
    start_y = 50
    line_height = 27
    
    # 遍历菜单项并绘制
    for i, item in enumerate(menu_items):
        lcd_draw_string(
            draw,
            x=20,
            y=start_y + i * line_height,
            text=item,
            color=(255, 255, 255),
            font_size=20,
            max_width=250,
            max_lines=1,
            clear_area=True
        )
    
    display.ShowImage(splash)
    
    if button.press_b():  # B键退出程序
        cap.release()
        break
        
    if button.press_d():  # D键更改颜色
        color = change_color()
        
    if button.press_a():  # A键进入调试模式
        while True:  # 调试模式循环
            splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
            draw = ImageDraw.Draw(splash)
            draw.rectangle([0, 0, display.width, display.height], fill=(15, 21, 46))
            debug_items = [
                display_texts[la]['debug_title'].format(color),
                display_texts[la]['current_dist'].format(x_distance),
                display_texts[la]['decrease'],
                display_texts[la]['increase'], 
                display_texts[la]['save'],
                display_texts[la]['exit_debug']
            ]
            
            start_y = 30
            line_height = 27
            
            # 遍历绘制调试菜单
            for i, item in enumerate(debug_items):
                lcd_draw_string(
                    draw,
                    x=20,
                    y=start_y + i * line_height,
                    text=item,
                    color=(255, 255, 255),
                    font_size=20,
                    max_width=230,
                    max_lines=1,
                    clear_area=True
                )
            display.ShowImage(splash)
            
            if button.press_c():  # C键减小距离
                x_distance -= 0.5
                print(f'前后距离减小为:{x_distance}')
            if button.press_d():  # D键增大距离
                x_distance += 0.5
                print(f'前后距离增大为:{x_distance}')
            if button.press_a():  # A键保存设置
                save_variable_value(x_distance, file_path='x_distance.txt')
                print('设置已保存!')
                lcd_draw_string(
                    draw,
                    x=200,
                    y=100,
                    text=display_texts[la]['saved'],
                    color=(0, 255, 0),
                    font_size=24,
                    max_width=100,
                    max_lines=1,
                    clear_area=True
                )
                
                display.ShowImage(splash)                
                time.sleep(1)
            if button.press_b():  # B键退出调试模式
                break
            time.sleep(0.1)
            
    if button.press_c():  # C键进入抓取模式
        print("进入抓取模式...")
        while True:
            # 恢复摄像头可视化
            ret, image = cap.read()
            if ret:
                # 显示摄像头画面
                b, g, r = cv2.split(image)
                image = cv2.merge((r, g, b))
                img = Image.fromarray(image)
                display.ShowImage(img)
                
            stop = Image_Processing(dog, color, mintime_yaw, mintime_x, cap, xdistance=x_distance, x_center=x_center)
            if stop == 0:
                dog.translation('x', 0)
                dog.translation('y', 0)
                dog.attitude('y', 0)
                dog.attitude('p', 0)
                down_arm(dog)
                time.sleep(2)
                break
            if button.press_b():  # B键退出抓取模式
                print("退出抓取模式")
                break
            time.sleep(0.1)


cap.release()
dog.reset()
exit()