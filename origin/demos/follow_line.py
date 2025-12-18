'''
巡线代码
可视化相关的代码已经注释
需要根据光照调节掩码范围
'''
#!/usr/bin/env python
# encoding: utf-8
import time
import cv2 as cv
import numpy as np
from picamera2 import Picamera2
from uiutils import *
from xgolib import XGO
from statistics import mode, StatisticsError
import logging
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image, ImageDraw, ImageFont
from uiutils import *
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width), "black")
display.ShowImage(splash)
button = Button()


# 定义颜色跟踪类
class color_follow:
    def __init__(self):
        """
        初始化一些参数
        binary: 二值化图像
        Center_x: 检测到的圆形的中心x坐标
        Center_y: 检测到的圆形的中心y坐标
        Center_r: 检测到的圆形的半径
        """
        self.binary = None
        self.Center_x = 0
        self.Center_y = 0
        self.Center_r = 0

    def line_follow(self, rgb_img, hsv_msg):
        """
        对输入的RGB图像进行跟踪
        :param rgb_img: 输入的RGB图像
        :param hsv_msg: HSV颜色范围的元组，格式为((H1, S1, V1), (H2, S2, V2))
        :return: 处理后的RGB图像、二值图像以及检测到的圆形的中心坐标和半径
        """
        height, width = rgb_img.shape[:2]
        img = rgb_img.copy()
        img[0:int(5*height / 8), 0:width] = 0  # 清空图像上半部分
        hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)  # 将图像转换为HSV

        # 创建掩码，保留黑色 需要根据光照条件稍微更改掩码范围
        lower_black = np.array([0, 0, 0], dtype="uint8")
        upper_black = np.array([180, 255, 30], dtype="uint8")
        mask = cv.inRange(hsv_img, lower_black, upper_black)


        color_mask = cv.bitwise_and(hsv_img, hsv_img, mask=mask)
        gray_img = cv.cvtColor(color_mask, cv.COLOR_RGB2GRAY)  
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5)) 
        gray_img = cv.morphologyEx(gray_img, cv.MORPH_CLOSE, kernel)



        ret, binary = cv.threshold(gray_img, 10, 255, cv.THRESH_BINARY) 
        find_contours = cv.findContours(
            binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # 获取轮廓点集(坐标)
        if len(find_contours) == 3:
            contours = find_contours[1]
        else:
            contours = find_contours[0]

        if len(contours) != 0:
            areas = []
            for c in range(len(contours)):
                areas.append(cv.contourArea(contours[c]))
            max_id = areas.index(max(areas))
            max_rect = cv.minAreaRect(contours[max_id])
            max_box = cv.boxPoints(max_rect)
            max_box = np.int0(max_box)

            box = cv.boxPoints(max_rect)  
            box = np.int0(box) 

            cv.drawContours(rgb_img, [box], 0, (255, 0, 0), 2)  # 绘制最小矩形

            (color_x, color_y), color_radius = cv.minEnclosingCircle(max_box)
            self.Center_x = int(color_x)  
            self.Center_y = int(color_y)
            self.Center_r = int(color_radius)
            cv.circle(rgb_img, (self.Center_x, self.Center_y),
                      5, (255, 0, 255), -1)
            b, g, r1 = cv.split(rgb_img)
            image = cv.merge((r1, g, b))
            imgok = Image.fromarray(image)
            display.ShowImage(imgok)
        else:
            self.Center_x = 0
            self.Center_y = 0
            self.Center_r = 0
        return rgb_img, binary, (self.Center_x, self.Center_y, self.Center_r)

# 定义简单PID控制器类
class simplePID:
    """
    非常简单的离散PID控制器
    """

    def __init__(self, target, P, I, D):
        """
        创建一个离散PID控制器

        :param target: 目标值，可以是标量或与P、I、D长度相同的向量
        :param P: 比例系数
        :param I: 积分系数
        :param D: 微分系数
        """
        # 检查参数形状是否兼容
        if (not (np.size(P) == np.size(I) == np.size(D)) or ((np.size(target) == 1) and np.size(P) != 1) or (
                np.size(target) != 1 and (np.size(P) != np.size(target) and (np.size(P) != 1)))):
            raise TypeError('input parameters shape is not compatable')

        self.Kp = np.array(P)
        self.Ki = np.array(I)
        self.Kd = np.array(D)
        self.last_error = 0
        self.integrator = 0
        self.timeOfLastCall = None
        self.setPoint = np.array(target)
        self.integrator_max = float('inf')
        

    def update(self, current_value):
        """
        更新PID控制器

        :param current_value: 当前值，可以是标量或与目标值长度相同的向量
        :return: 控制信号，与目标值长度相同的向量
        """
        current_value = np.array(current_value)
        if (np.size(current_value) != np.size(self.setPoint)):
            raise TypeError(
                'current_value and target do not have the same shape')
        if (self.timeOfLastCall is None):
            # PID首次调用，还不知道时间间隔deltaT，不应用控制信号
            self.timeOfLastCall = time.perf_counter()
            return np.zeros(np.size(current_value))
        error = self.setPoint - current_value
        P = error
        currentTime = time.perf_counter()
        deltaT = (currentTime - self.timeOfLastCall)
        # 误差的积分是当前误差乘以自上次更新以来的时间
        self.integrator = self.integrator + (error * deltaT)
        I = self.integrator
        # 导数是误差的差值除以自上次更新以来的时间
        D = (error - self.last_error) / deltaT
        self.last_error = error
        self.timeOfLastCall = currentTime
        # 返回控制信号
        return self.Kp * P + self.Ki * I + self.Kd * D


# 定义巡线检测类
class LineDetect:
    def __init__(self):
        self.img = None
        self.circle = ()
        self.Roi_init = ()
        self.scale = 1000
        list_hsv = (0, 43, 46, 10, 255, 255)
        self.hsv_text = ((int(list_hsv[0]), int(list_hsv[1]), int(list_hsv[2])),
                         (int(list_hsv[3]), int(list_hsv[4]), int(list_hsv[5])))
        self.hsv_range = self.hsv_text
        self.dyn_update = True
        self.select_flags = False
        self.Track_state = 'tracking'
        self.windows_name = 'frame'
        self.color = color_follow()
        self.cols, self.rows = 0, 0
        self.FollowLinePID = (50, 0, 30)
        self.PID_init()
        self.dog = XGO(port='/dev/ttyAMA0', version="xgolite")
        self.dog_type = 'L'
        self.dog_init()
        
    def execute(self, point_x, point_y, radius):
        """
        根据检测到的圆形信息，通过PID控制器控制机械狗转向
        :param point_x: 检测到的圆形的x坐标
        :param point_y: 检测到的圆形的y坐标
        :param radius: 检测到的圆形的半径
        """
        [z_Pid, _] = self.PID_controller.update([(point_x - 160), 0])  #如果狗的运动在线的左边，需要调小150，反之增大。
        if self.dog_type == 'L':
            runtime_x = 0.2
            runtime_x += 0.05*abs(int(z_Pid))
            runtime_x = min(abs(runtime_x),0.9)
            turn_speed = int(max(min(5 * abs(z_Pid), 48), 50))
        else:
            runtime_x = 0.3
            runtime_x += 0.02*abs(int(z_Pid))
            runtime_x = min(abs(runtime_x),0.8)
            turn_speed = int(min(1.1 * abs(z_Pid), 18))
        if abs(z_Pid) < 8:  # 当转向角度较小时，前进
            self.dog.turn(0)
            # self.dog.gait_type(mode)
            self.dog.move_x(18)
        elif abs(z_Pid)>=8:
            fuhao = abs(z_Pid)/z_Pid
            turn_speed = fuhao * turn_speed
            self.dog.turn(turn_speed)
            run_speed = 15
            logging.warning(f'转向角{z_Pid},转向速度{turn_speed},前进速度{run_speed},运动调整时间{runtime_x}')
            self.dog.move_x(run_speed)
            time.sleep(runtime_x)
        else:
            self.dog.stop()

    def cancel(self):
        """
        重置机械狗的状态
        """
        self.dog.reset()

    def dog_init(self):
        """
        初始化机械狗的状态，包括停止、设置速度、调整位置和角度等
        """
        fm = self.dog.read_firmware()
        print(fm)
        if fm[0] == 'M':
            print('XGO-MINI')
            self.dog = XGO(port='/dev/ttyAMA0', version="xgomini")
            self.dog_type = 'M'
        else:
            print('XGO-LITE')
            self.dog = XGO(port='/dev/ttyAMA0', version="xgolite")
            self.dog_type = 'L'
        self.dog.stop()
        self.dog.pace('normal')
        self.dog.gait_type("slow_trot")
        self.dog.translation('z', 75)
        self.dog.attitude('p', 15)
        time.sleep(2)

    def process(self, rgb_img, action):
        """
        处理输入的RGB图像，根据按键事件和跟踪状态进行相应操作

        :param rgb_img: 输入的RGB图像
        :param action: 动作值（当前未充分使用，可后续扩展）
        :return: 处理后的RGB图像和二值图像
        """
        binary = []
        rgb_img = cv.resize(rgb_img, (320, 240))
        if button.press_d():
            self.Track_state = 'init'
            print('state:init')
        if button.press_c():
            self.Track_state = 'color'
            print('state:color')
        if button.press_a():
            self.Track_state = 'tracking'
            print('state:tracking')

        if self.Track_state == 'tracking':
            # print(self.hsv_range)
            rgb_img, binary, self.circle = self.color.line_follow(rgb_img, self.hsv_range)
            if len(self.circle) != 0:
                #print('检测到线条，巡线运动')
                self.execute(self.circle[0], self.circle[1], self.circle[2])
            else:
                print('未检测到线条，停止')
                self.dog.stop()  # 未检测到线条，停止
        return rgb_img, binary

    def Reset(self):
        """
        重置巡线检测的相关状态和参数，包括PID控制器、跟踪状态、HSV范围和机械狗状态等
        """
        self.PID_init()
        self.Track_state = 'init'
        self.hsv_range = ()
        self.dog_init()

    def PID_init(self):
        """
        初始化PID控制器的参数
        """
        self.PID_controller = simplePID(
            [0, 0],
            [self.FollowLinePID[0] / 1.0 / self.scale, 0],
            [self.FollowLinePID[1] / 1.0 / self.scale, 0],
            [self.FollowLinePID[2] / 1.0 / self.scale, 0])

#------------------屏幕初始化-------------------


if __name__ == '__main__':
    font = cv.FONT_HERSHEY_SIMPLEX
    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    print("摄像头初始化完毕")
    line_detect = LineDetect()

    try:
        while True:
            start = time.time()
            ret, frame = cap.read()
            if not ret:
                print("无法捕获图像！")
                continue
            action = 32
            frame, binary = line_detect.process(frame, action)
            if button.press_b():
                line_detect.cancel()
                break

    except KeyboardInterrupt:
        print("程序被手动终止")
    finally:
        cap.release()
        print("摄像头已停止")