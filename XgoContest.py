import sys
import time
import math
import json
from xgolib import XGO
import numpy as np
import cv2
import spidev as SPI
import LCD_2inch
from key import Button
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
import pyzbar.pyzbar as pyzbar

__version__ = '1.0.13'
__last_modified__ = '2023/5/4'


class XgoExtend(XGO):
    def __init__(self, port, screen, button, cap, baud=115200, version='xgomini'):
        super().__init__(port, baud, version)
        self.version = version
        fm = self.read_firmware()
        if fm[0] == 'L':
            super().__init__(port, baud, 'xgolite')
            self.version = 'xgolite'
        self.reset()
        time.sleep(0.5)
        self.init_yaw = self.read_yaw()
        self.screen = screen
        self.button = button
        self.mintime = 0.65
        self.cap = cap
        self.calibration = {}
        try:
            with open("calibration.json", 'r', encoding='utf-8') as f:
                self.k = json.load(f)
            self.block_k1 = self.k["BLOCK_k1"]
            self.block_k2 = self.k["BLOCK_k2"]
            self.block_b = self.k["BLOCK_b"]
            self.block_ky = self.k["BLOCK_ky"]
            self.block_by = self.k["BLOCK_by"]
            self.cup_k1 = self.k["CUP_k1"]
            self.cup_k2 = self.k["CUP_k2"]
            self.cup_b = self.k["CUP_b"]
        except Exception as e:
            print("Error!Can't load position json!")
            print("Error:", e)

    def show_img(self, img, img_mode='RGB'):
        imgok = Image.fromarray(img, mode=img_mode)
        self.screen.ShowImage(imgok)

    def check_quit(self):
        if self.button.press_b():
            self.cap.release()
            cv2.destroyAllWindows()
            sys.exit()

    def move_by(self, distance, vx, vy, k, mintime):
        runtime = k * abs(distance) + mintime
        self.move_x(math.copysign(vx, distance))
        self.move_y(math.copysign(vy, distance))
        time.sleep(runtime)
        self.move_x(0)
        self.move_y(0)
        time.sleep(0.2)

    def move_x_by(self, distance, vx=18, k=0.035, mintime=0.55):
        self.move_by(distance, vx, 0, k, mintime)
        pass

    def move_y_by(self, distance, vy=18, k=0.0373, mintime=0.5):
        self.move_by(distance, 0, vy, k, mintime)
        pass

    def adjust_x(self, distance, vx=18, k=0.045, mintime=0.6):
        self.move_by(distance, vx, 0, k, mintime)
        pass

    def adjust_y(self, distance, vy=18, k=0.0373, mintime=0.5):
        self.pace('slow')
        self.move_by(distance, 0, vy, k, mintime)
        self.pace('normal')
        pass

    def adjust_yaw(self, theta, mintime, vyaw=16, k=0.08):
        runtime = abs(theta) * k + mintime
        self.turn(math.copysign(vyaw, theta))
        time.sleep(runtime)
        self.turn(0)
        pass

    def turn_to(self, theta, vyaw=60, emax=10):
        cur_yaw = self.read_yaw()
        des_yaw = self.init_yaw + theta
        while abs(des_yaw - cur_yaw) >= emax:
            self.turn(math.copysign(vyaw, des_yaw - cur_yaw))
            cur_yaw = self.read_yaw()
            print(cur_yaw)
        self.turn(0)
        time.sleep(0.2)
        pass

    def adjust_turn_to(self, theta, vyaw=30, emax=3):
        self.pace('slow')
        cur_yaw = self.read_yaw()
        des_yaw = self.init_yaw + theta
        while abs(des_yaw - cur_yaw) >= emax:
            self.turn(math.copysign(vyaw, des_yaw - cur_yaw))
            cur_yaw = self.read_yaw()
            print(cur_yaw)
        self.turn(0)
        self.pace('normal')
        time.sleep(0.2)
        pass

    # des_x=14, emax_x=1.8, emax_y=1.9, emax_yaw=3.5, mintime=0.6
    def prepare_for_block(self, x, y, angle, des_x, emax_x, emax_y, emax_yaw, min_time):
        e_x = x - des_x
        if angle > emax_yaw:
            self.adjust_yaw(-angle, min_time)
            # if y < 4 and x > 16.5:
            #     time.sleep(0.3)
            #     self.adjust_y(2)
        elif angle < -emax_yaw:
            self.adjust_yaw(-angle, min_time)
            # if y > -4 and x > 16.5:
            #     time.sleep(0.3)
            #     self.adjust_y(-2)
        else:
            if abs(y) > emax_y:
                self.move_y_by(-y, vy=14)
            else:
                if abs(e_x) > emax_x:
                    self.move_x_by(e_x, vx=16, mintime=min_time)
                else:
                    print("DONE BLOCK")
                    self.action(0x83)
                    time.sleep(8.5)
                    self.reset()
                    time.sleep(0.5)
                    return True
        return False

    def prepare_for_cup(self, x1, x2, y1, y2, vx_k, des_x=16, emax_y=1.8):
        if abs(y1 + y2) > emax_y:
            self.move_y_by(-(y1 + y2) / 2)
            time.sleep(0.3)
        else:
            if 23 < (x1 + x2) / 2 < 60:  # 过滤掉误识别数据
                self.move_x_by((x1 + x2) / 2 - des_x, k=vx_k, mintime=0.65)
                print("DONE CUP")
                self.action(0x84)
                time.sleep(8)
                return True
        return False

    def prepare_for_bridge(self, x, y, vx_k, action, emax_y=8):
        if x > 15:
            self.move_x_by(3, mintime=0.65)
        else:
            if abs(y) > emax_y:
                bias_y = 0.125 * y
                if bias_y > 7:
                    bias_y = 7
                if bias_y < -7:
                    bias_y = -7
                self.adjust_y(-bias_y, mintime=1)
            else:
                self.control_3v3('off')
                self.attitude('p', 0)
                time.sleep(0.5)
                if action == 0x87:
                    self.move_x_by(x * 0.6, mintime=0.65, k=vx_k)
                else:
                    self.move_x_by(x, mintime=0.65, k=vx_k)
                # print("DONE BRIDGE")
                self.action(action)
                time.sleep(8)
                return True
        return False

    def cal_block(self, s_x, s_y):
        # k1 = 0.00323
        # k2 = -1.272
        # b = 139.5
        # # k1 = 0.002875
        # # k2 = -1.061
        ky = 0.00574
        # b = 108.1
        # x = k1 * s_x * s_x + k2 * s_x + b
        # y = (ky * x + 0.01) * (s_y - 160)
        x = self.block_k1 * s_x * s_x + self.block_k2 * s_x + self.block_b
        # y = self.block_ky * (s_y - 160) * x + self.block_by
        y = (ky * x + 0.01) * (s_y - 160)
        return x, y

    def cal_cup(self, width1, width2, cup_y1, cup_y2):
        kw1 = 1.453e-05
        kw2 = - 1.461e-05
        kc1 = 0.0146
        kc2 = -1.81
        ky = 0.006418
        by = -0.007943
        bc = 77.71
        # 横向畸变
        # kwidth1 = kw1 * (cup_y1 - 160) * (cup_y1 - 160) - kw2 * abs(cup_y1 - 160) + 1
        # kwidth2 = kw1 * (cup_y2 - 160) * (cup_y2 - 160) - kw2 * abs(cup_y2 - 160) + 1
        # width1 = width1 / kwidth1
        # width2 = width2 / kwidth2
        x1 = self.cup_k1 * width1 * width1 + self.cup_k2 * width1 + self.cup_b
        x2 = self.cup_k1 * width2 * width2 + self.cup_k2 * width2 + self.cup_b
        y1 = (ky * x1 - by) * (cup_y1 - 160)
        y2 = (ky * x2 - by) * (cup_y2 - 160)
        return x1, x2, y1, y2

    def get_color_mask(self, color):
        # if color in ['cup_red', 'cup_blue', 'cup_green']:
        #     color_upper = np.array(self.color_mask[color][0])
        #     color_lower = np.array(self.color_mask[color][1])
        # if color == 'red':
        #     color_lower = np.array([173, 90, 46])
        #     color_upper = np.array([183, 255, 255])
        # elif color == 'green':
        #     color_lower = np.array([73, 150, 70])
        #     color_upper = np.array([88, 255, 255])
        # elif color == 'blue':
        #     color_lower = np.array([100, 100, 50])
        #     color_upper = np.array([110, 255, 255])
        if color == 'red':
            color_lower = (0, 145, 132)
            color_upper = (255, 255, 255)
        # elif color == 'green':
        #     color_lower = (40, 0, 130)
        #     color_upper = (200, 110, 230)
        if color == 'blue':
            color_lower = (10, 0, 0)
            color_upper = (200, 136, 120)
        return color_upper, color_lower

    def filter_img(self, frame, color):
        if isinstance(color, list):
            b, g, r = cv2.split(frame)
            frame = cv2.merge((r, g, b))
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            color_lower = np.array(color[0])
            color_upper = np.array(color[1])
            mask = cv2.inRange(hsv, color_lower, color_upper)
        else:
            if color == 'green':
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                color_lower = np.array([70, 120, 80])
                color_upper = np.array([90, 255, 255])
                mask = cv2.inRange(hsv, color_lower, color_upper)
            else:
                frame = cv2.GaussianBlur(frame, (3, 3), 1)
                color_upper, color_lower = self.get_color_mask(color)
                frame_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                mask = cv2.inRange(frame_lab, color_lower, color_upper)
        img_mask = cv2.bitwise_and(frame, frame, mask=mask)
        return img_mask

    def detect_contours(self, frame, color):
        img_mask = self.filter_img(frame, color)

        CANNY_THRESH_1 = 16
        CANNY_THRESH_2 = 120
        edges = cv2.Canny(img_mask, CANNY_THRESH_1, CANNY_THRESH_2)
        edges = cv2.dilate(edges, None, iterations=1)
        edges = cv2.erode(edges, None, iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours, img_mask

    def detect_block(self, contours):
        flag = False
        length, width, angle, s_x, s_y = 0, 0, 0, 0, 0
        for i in range(0, len(contours)):
            if cv2.contourArea(contours[i]) < 20 ** 2:  # 20 ** 2:
                continue
            rect = cv2.minAreaRect(contours[i])
            if 0.4 < rect[1][0] / rect[1][1] < 2.5:  #
                continue
            if not flag:
                if rect[2] > 45:
                    length = rect[1][0]
                    width = rect[1][1]
                    angle = rect[2] - 90
                else:
                    length = rect[1][1]
                    width = rect[1][0]
                    angle = rect[2]
                s_x = rect[0][1]  # s_代表屏幕坐标系
                s_y = rect[0][0]
                flag = True
            else:  # 识别出两个及以上的矩形退出
                flag = False
                break
        return flag, length, width, angle, s_x, s_y

    def detect_cup(self, contours):
        num = 0
        width1, width2, s_y1, s_y2 = 0, 0, 0, 0
        index = [0, 0]
        flag = True
        for i in range(0, len(contours)):
            if cv2.contourArea(contours[i]) < 20 ** 2:
                continue
            rect = cv2.minAreaRect(contours[i])
            if 0.6 < rect[1][0] / rect[1][1] < 1.65:
                if num == 2:
                    flag = False
                    break
                index[num] = i
                num += 1
        if flag and num == 2:
            c1 = contours[index[0]]
            c2 = contours[index[1]]
            rect1 = cv2.minAreaRect(c1)
            rect2 = cv2.minAreaRect(c2)
            if rect1[2] > 45:
                width1 = rect1[1][1]
            else:
                width1 = rect1[1][0]

            if rect2[2] > 45:
                width2 = rect2[1][1]
            else:
                width2 = rect2[1][0]
            s_y1 = rect1[0][0]
            s_y2 = rect2[0][0]
        else:
            flag = False
        return flag, width1, width2, s_y1, s_y2

    def detect_square(self, contours):
        num = 0
        width1, width2, s_y1, s_y2 = 0, 0, 0, 0
        index = [0, 0]
        flag = True
        for i in range(0, len(contours)):
            if cv2.contourArea(contours[i]) < 10 ** 2:
                continue
            rect = cv2.minAreaRect(contours[i])
            if 0.65 < rect[1][0] / rect[1][1] < 1.5:
                if num == 2:
                    flag = False
                    break
                index[num] = i
                num += 1
        if flag and num == 2:
            c1 = contours[index[0]]
            c2 = contours[index[1]]
            rect1 = cv2.minAreaRect(c1)
            rect2 = cv2.minAreaRect(c2)
            if rect1[2] > 45:
                width1 = rect1[1][1]
            else:
                width1 = rect1[1][0]

            if rect2[2] > 45:
                width2 = rect2[1][1]
            else:
                width2 = rect2[1][0]
            s_y1 = rect1[0][0]
            s_y2 = rect2[0][0]
        else:
            flag = False
        return flag, width1, width2, s_y1, s_y2

    def detect_single_cup(self, contours):
        flag = False
        length, width, angle, s_x, s_y = 0, 0, 0, 0, 0
        for i in range(0, len(contours)):
            if cv2.contourArea(contours[i]) < 15 ** 2:
                continue
            rect = cv2.minAreaRect(contours[i])
            if not (0.5 < rect[1][0] / rect[1][1] < 2):
                continue
            if not flag:
                if rect[2] > 45:
                    length = rect[1][0]
                    width = rect[1][1]
                    angle = rect[2] - 90
                else:
                    length = rect[1][1]
                    width = rect[1][0]
                    angle = rect[2]
                s_x = rect[0][1]
                s_y = rect[0][0]
                flag = True
            else:
                flag = False
                break
        return flag, width, s_y

    def search_for_block(self, color, des_x=14, emax_x=1.8, emax_y=1.8, emax_yaw=3.5, mintime=0.8, COUNT_MAX=18):
        count = 0
        length, width, angle, s_x, s_y = 0, 0, 0, 0, 0
        x, y = 0, 0
        self.attitude('p', 10)
        lost_count = 0
        while True:
            ret, frame = self.cap.read()
            self.check_quit()
            contours, img = self.detect_contours(frame, color)
            flag, temp_length, temp_width, temp_angle, temp_s_x, temp_s_y = self.detect_block(contours)
            if not flag:
                self.show_img(img)
                lost_count += 1
                if lost_count > 30:
                    lost_count = 0
                    self.move_x_by(-5)
                continue
            lost_count = 0
            cv2.putText(img, '%4.1f' % temp_s_x, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % temp_s_y, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % temp_angle, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % x, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % y, (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            self.show_img(img)
            count += 1
            length = (count - 1) * length / count + temp_length / count
            width = (count - 1) * width / count + temp_width / count
            angle = (count - 1) * angle / count + temp_angle / count
            s_x = (count - 1) * s_x / count + temp_s_x / count
            s_y = (count - 1) * s_y / count + temp_s_y / count
            if count == COUNT_MAX:
                count = 0
                x, y = self.cal_block(s_x, s_y)
                print("block position x: %4.1f, y: %4.1f" % (x, y))
                done = self.prepare_for_block(x, y, angle, des_x, emax_x, emax_y, emax_yaw, mintime)
                if done:
                    break

    def search_for_cup(self, color, COUNT_MAX=20, direction=0, k=0.04):
        count = 0
        width1, width2, s_y1, s_y2 = 0, 0, 0, 0
        x1, x2, y1, y2 = 0, 0, 0, 0
        lost_count = 0
        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            contours, img = self.detect_contours(frame, color)
            flag, temp_width1, temp_width2, temp_s_y1, temp_s_y2 = self.detect_cup(contours)
            if not flag:
                self.show_img(img)
                lost_count += 1
                if lost_count > 30:
                    lost_count = 0
                    self.move_x_by(-5)
                continue
            cv2.putText(img, '%4.1f' % x1, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % x2, (90, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % y1, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % y2, (90, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            self.show_img(img)
            lost_count = 0
            count += 1
            width1 = (count - 1) * width1 / count + temp_width1 / count
            width2 = (count - 1) * width2 / count + temp_width2 / count
            s_y1 = (count - 1) * s_y1 / count + temp_s_y1 / count
            s_y2 = (count - 1) * s_y2 / count + temp_s_y2 / count
            if count == COUNT_MAX:
                count = 0
                x1, x2, y1, y2 = self.cal_cup(width1, width2, s_y1, s_y2)
                print("x1: %4.2f, x2: %4.2f, y1: %4.2f, y2: %4.2f" % (x1, x2, y1, y2))
                done = False
                done = self.prepare_for_cup(x1, x2, y1, y2, vx_k=k)
                if direction != 0:
                    self.turn_to(direction, vyaw=30, emax=2)
                if done:
                    break

    def detect_block_color(self, color=None):
        red_count, green_count, blue_count = 0, 0, 0
        lost_count = 0
        none_count = 0
        color_count = 0
        self.attitude('p', 10)
        while True:
            self.check_quit()
            ret, frame = self.cap.read()

            if color is None:
                if red_count > 30:
                    self.reset()
                    return 'red'

                if green_count > 45:
                    self.reset()
                    return 'green'

                if blue_count > 30:
                    self.reset()
                    return 'blue'

                contours, img = self.detect_contours(frame, 'red')
                flag, _, _, _, _, _ = self.detect_block(contours)
                if flag:
                    red_count += 1
                    lost_count = 0
                    continue

                contours, img = self.detect_contours(frame, 'green')
                flag, _, _, _, _, _ = self.detect_block(contours)
                if flag:
                    green_count += 1
                    lost_count = 0
                    continue

                contours, img = self.detect_contours(frame, 'blue')
                flag, _, _, _, _, _ = self.detect_block(contours)
                if flag:
                    blue_count += 1
                    lost_count = 0
                    continue
            else:
                contours, img = self.detect_contours(frame, color)
                flag, _, _, _, _, _ = self.detect_block(contours)
                if flag:
                    color_count += 1
                    lost_count = 0
                    if color_count == 30:
                        self.reset()
                        return True
                    continue

            lost_count += 1
            if lost_count > 30:
                lost_count = 0
                none_count += 1
                if none_count == 2:
                    self.reset()
                    return False
                self.pace('slow')
                self.move_x_by(-12)
        return False

    def search_for_cup_CQ(self, color1, color2, COUNT_MAX=25, direction=None, k=0.035):
        count = 0
        width1, width2, s_y1, s_y2 = 0, 0, 0, 0
        x1, x2, y1, y2 = 0, 0, 0, 0
        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            contours, img = self.detect_contours(frame, color1)
            flag, temp_width1, temp_s_y1 = self.detect_single_cup(contours)
            if not flag:
                self.show_img(img)
                continue

            ret, frame = self.cap.read()
            contours, img = self.detect_contours(frame, color2)
            flag, temp_width2, temp_s_y2 = self.detect_single_cup(contours)
            if not flag:
                self.show_img(img)
                continue
            cv2.putText(img, '%4.1f' % x1, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % x2, (90, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % y1, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img, '%4.1f' % y2, (90, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            self.show_img(img)

            count += 1
            width1 = (count - 1) * width1 / count + temp_width1 / count
            width2 = (count - 1) * width2 / count + temp_width2 / count
            s_y1 = (count - 1) * s_y1 / count + temp_s_y1 / count
            s_y2 = (count - 1) * s_y2 / count + temp_s_y2 / count
            if count == COUNT_MAX:
                count = 0
                x1, x2, y1, y2 = self.cal_cup(width1, width2, s_y1, s_y2)
                print("x1: %4.2f, x2: %4.2f, y1: %4.2f, y2: %4.2f" % (x1, x2, y1, y2))
                done = False
                done = self.prepare_for_cup(x1, x2, y1, y2, vx_k=k)
                if direction is not None:
                    self.turn_to(direction, vyaw=30, emax=2)
                if done:
                    break

    def calibration_block(self, color, COUNT_MAX=25):
        count = 0
        block_num = 0
        state = 0
        path = 'calibration.json'
        s_x = 0
        s_y = 0
        s_x_list = [186, 174.5, 163.5, 150.5, 143.5, 138.5, 131.5, 125.6]
        x_list = [13, 15, 17, 20, 22, 24, 27, 30]

        ky_list = []
        y_list = [2.25, 0.25, -1.75, 0.25, 2.25, 0.25, -1.75, 0.25]
        kx_list = []
        self.attitude('p', 10)
        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            contours, img = self.detect_contours(frame, color)
            if state == 0:
                cv2.putText(img, 'Put BLOCK in', (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 0, 200), 2)
                cv2.putText(img, '- ' + str(block_num + 1) + ' -', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2,
                            (200, 0, 200), 2)
                cv2.putText(img, 'Then press B', (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
                self.show_img(img)
                if self.button.press_d():
                    state = 1
                    time.sleep(0.5)
            elif state == 1:
                flag, temp_length, temp_width, temp_angle, temp_s_x, temp_s_y = self.detect_block(contours)
                if not flag:
                    self.show_img(img)
                    continue
                cv2.putText(img, 'Detecting......', (30, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 200), 2)
                cv2.putText(img, '%4.1f' % temp_s_x, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
                cv2.putText(img, '%4.1f' % temp_s_y, (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
                self.show_img(img)
                count += 1
                s_x = s_x * (count - 1) / count + temp_s_x / count
                s_y = s_y * (count - 1) / count + temp_s_y / count
                if count == COUNT_MAX:
                    count = 0
                    s_x_list.append(s_x)
                    s_x_list.append(s_x)
                    ky_list.append(y_list[block_num])
                    kx_list.append((s_y - 160) * (14 + block_num * 3))
                    x_list.append(14 + block_num * 3)
                    x_list.append(14 + block_num * 3)
                    block_num += 1
                    state = 0
                    print("Finish" + str(block_num))
                    if block_num == 8:
                        z = np.polyfit(s_x_list, x_list, 2)
                        self.calibration["BLOCK_k1"] = z[0]
                        self.calibration["BLOCK_k2"] = z[1]
                        self.calibration["BLOCK_b"] = z[2]
                        z = np.polyfit(kx_list, ky_list, 1)
                        self.calibration["BLOCK_ky"] = z[0]
                        self.calibration["BLOCK_by"] = z[1]
                        break

    def calibration_cup(self, color, COUNT_MAX=25):
        count = 0
        cap_num = 0
        state = 0
        path = 'calibration.json'
        width1 = 0
        width2 = 0
        width_list = []
        x_list = []

        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            contours, img = self.detect_contours(frame, color)
            if state == 0:
                cv2.putText(img, 'Put Two Cups In', (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 0, 200), 2)
                cv2.putText(img, '- ' + str(cap_num + 1) + ' -', (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2,
                            (200, 0, 200), 2)
                cv2.putText(img, 'Then press B', (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
                self.show_img(img)
                if self.button.press_d():
                    state = 1
                    time.sleep(0.5)
            elif state == 1:
                flag, temp_width1, temp_width2, temp_s_y1, temp_s_y2 = self.detect_cup(contours)
                if not flag:
                    self.show_img(img)
                    continue
                cv2.putText(img, 'Detecting......', (30, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 0, 200), 2)
                self.show_img(img)
                count += 1
                width1 = width1 * (count - 1) / count + temp_width1 / count
                width2 = width2 * (count - 1) / count + temp_width2 / count
                if count == COUNT_MAX:
                    count = 0
                    width_list.append(width1)
                    width_list.append(width2)
                    x_list.append(24.7 + cap_num * 2)
                    x_list.append(24.7 + cap_num * 2)
                    cap_num += 1
                    state = 0
                    print("Finish" + str(cap_num))
                    if cap_num == 8:
                        z = np.polyfit(width_list, x_list, 2)
                        self.calibration["CUP_k1"] = z[0]
                        self.calibration["CUP_k2"] = z[1]
                        self.calibration["CUP_b"] = z[2]
                        with open(path, 'w', encoding='utf-8') as f:
                            json.dump(self.calibration, f)
                        break

    def calibration_contest(self, color='red'):
        self.calibration_block(color)
        self.reset()
        time.sleep(1)
        self.calibration_cup(color)

    def show_filter_img(self, lower, upper):
        while True:
            ret, frame = self.cap.read()
            b, g, r = cv2.split(frame)
            img = cv2.merge((r, g, b))
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            color_lower = np.array(lower)
            color_upper = np.array(upper)
            mask = cv2.inRange(hsv, color_lower, color_upper)
            img_mask = cv2.bitwise_and(img, img, mask=mask)
            if self.button.press_c():
                lower[0] = max(lower[0] - 5, 0)
                upper[0] = max(upper[0] - 5, 10)
                time.sleep(0.5)
            if self.button.press_d():
                lower[0] = min(lower[0] + 5, 245)
                upper[0] = min(upper[0] + 5, 255)
                time.sleep(0.5)
            cv2.putText(img_mask, 'up:{},{},{}'.format(upper[0], upper[1], upper[2]), (20, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            cv2.putText(img_mask, 'low:{},{},{}'.format(lower[0], lower[1], lower[2]), (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
            self.show_img(img_mask)
            self.check_quit()

    def set_move_mintime(self, mintime):
        self.mintime = mintime

    def detect_QR(self, action, count_max=20, direction=None, k=0.035):
        self.attitude('p', 15)
        self.control_3v3('on')
        lower = [153, 20, 16]
        upper = [203, 255, 255]
        count = 0
        avg_x, avg_y, avg_w = 0, 0, 0
        while True:
            self.check_quit()
            ret, img = self.cap.read()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            color_lower = np.array(lower)
            color_upper = np.array(upper)
            mask = cv2.inRange(hsv, color_lower, color_upper)
            img = cv2.bitwise_and(img, img, mask=mask)

            CANNY_THRESH_1 = 4
            CANNY_THRESH_2 = 50
            edges = cv2.Canny(img, CANNY_THRESH_1, CANNY_THRESH_2)
            edges = cv2.dilate(edges, None, iterations=6)
            edges = cv2.erode(edges, None, iterations=2)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            square_count = 0
            x, y, h, w = 0, 0, 0, 0
            for i in range(0, len(contours)):
                if cv2.contourArea(contours[i]) < 300:
                    continue
                square_count = square_count + 1
                if square_count > 1:
                    break
                rect = cv2.minAreaRect(contours[i])
                h = int(rect[1][0])
                w = int(rect[1][1])
                if rect[2] < 45:
                    tempVar = h
                    h = w
                    w = tempVar
                x = rect[0][0]
                y = rect[0][1]

                cv2.rectangle(img, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (255, 255, 255),
                              2)
            if square_count != 1:
                continue
            count += 1
            avg_x = (count - 1) / count * avg_x + x / count
            avg_y = (count - 1) / count * avg_y + y / count
            avg_w = (count - 1) / count * avg_w + w / count
            if count == count_max:
                count = 0
                if avg_y > 193:
                    self.move_x_by(-1)
                    continue
                print("x: %4.1f, y: %4.1f, w: %4.1f" % (avg_x, avg_y, avg_w))
                x = 0.001379 * avg_y * avg_y - 0.5879 * avg_y + 71.8
                y = avg_x - 160
                done = False
                done = self.prepare_for_bridge(x, y, k, action)
                if done:
                    break
                if direction is not None:
                    self.adjust_turn_to(direction, vyaw=30, emax=2)
            self.show_img(img)

    def search_ball(self):
        self.reset()
        color_mask = self.cap_color_mask()
        time.sleep(2)
        while True:
            self.detect_ball(color_mask)
            time.sleep(2)
            self.throw_ball()

    def cap_color_mask(self, position=[160, 100], scale=25, h_error=20, s_limit=[90, 255], v_limit=[90, 230]):
        count = 0
        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            if self.button.press_d() and count == 0:
                count += 1
                color = np.mean(h[position[1]:position[1] + scale, position[0]:position[0] + scale])
                color_lower = [max(color - h_error, 0), s_limit[0], v_limit[0]]
                color_upper = [min(color + h_error, 255), s_limit[1], v_limit[1]]
                return [color_lower, color_upper]
            img = cv2.flip(frame, 1)
            if count == 0:
                cv2.rectangle(img, (position[0], position[1]), (position[0] + scale, position[1] + scale),
                              (255, 255, 255), 2)
                cv2.putText(img, 'press button B', (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            b, g, r = cv2.split(img)
            img = cv2.merge((r, g, b))
            self.show_img(img)

    def detect_ball(self, color_mask, COUNT_MAX=14, p1=36, p2=15, minR=6, maxR=35):
        count = 0
        lost_count = 0
        x, y, r = 0, 0, 0
        color_lower = np.array(color_mask[0])
        color_upper = np.array(color_mask[1])
        self.attitude('p', 10)
        self.translation('z', 80)
        self.translation('x', 10)
        while True:
            self.check_quit()
            ret, frame = self.cap.read()
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, color_lower, color_upper)

            img = cv2.bitwise_and(frame, frame, mask=mask)
            img = cv2.flip(img, 1)

            image = cv2.medianBlur(img, 5)
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(gray_img, cv2.HOUGH_GRADIENT, 1, 20, param1=p1, param2=p2, minRadius=minR,
                                       maxRadius=maxR)
            if circles is not None:
                if len(circles[0]) != 1:
                    continue
                for i in circles[0]:
                    count += 1
                    lost_count = 0
                    temp_x, temp_y, temp_r = int(i[0]), int(i[1]), int(i[2])
                    cv2.circle(img, (temp_x, temp_y), temp_r, (255, 255, 255), 2)
                    cv2.circle(img, (temp_x, temp_y), 2, (255, 255, 255), 2)
                    x = x * (count - 1) / count + temp_x / count
                    y = y * (count - 1) / count + temp_y / count
                    r = r * (count - 1) / count + temp_r / count
            else:
                lost_count += 1
                if lost_count == 40:
                    lost_count = 0
                    self.adjust_x(-1, vx=12)
            if count == COUNT_MAX:
                count = 0
                print("y:{}".format(y))
                done = self.grab_ball(x, y, r)
                if done:
                    return True

            b, g, r = cv2.split(img)
            img = cv2.merge((r, g, b))
            self.show_img(img)

    def grab_ball(self, x, y, r, des_y=170, err_x_max=7, err_y_max=5, vk=0.035, min_time=0.7):
        if self.version == 'xgomini':
            min_time = min_time * 0.8
        err_x = x - 160
        err_y = des_y - y
        if err_x > 0:
            angle = min(0.035 * err_x, 8)
        else:
            angle = max(0.035 * err_x, -8)

        if err_y > 0:
            distance = min(0.12 * err_y, 7)
        else:
            distance = max(0.02 * err_y, -5)
        if y < 150:
            self.adjust_x(3, vx=7, mintime=min_time, k=vk)
            return False

        if abs(err_x) > err_x_max:
            if self.version == 'xgolite':
                self.adjust_yaw(angle, min_time + 0.3, k=vk)
            else:
                self.adjust_yaw(angle, min_time + 0.1, k=vk)
        else:
            if abs(err_y) > err_y_max:
                if distance < 0:
                    self.adjust_x(distance, vx=7, mintime=min_time, k=vk)
                else:
                    self.adjust_x(distance, vx=13, mintime=min_time, k=vk)
            else:
                if abs(err_x) > err_x_max * 0.8:
                    self.adjust_yaw(angle, min_time, k=vk)
                self.adjust_x(2, vx=12, mintime=min_time, k=vk)
                self.action(0x83)
                time.sleep(8.5)
                return True
        return False

    def throw_ball(self):
        self.motor_speed(255)
        self.attitude('p', 10)
        self.arm(130, 0)
        time.sleep(1)
        self.claw(0)
        time.sleep(2)
        self.arm(80, 80)
        time.sleep(0.5)
        self.reset()
        time.sleep(1)

    # def calibration_color(self):
    #     path = 'color_mask.json'
    #     stage = ['cup_red', 'cup_green', 'cup_blue']
    #     color_mask = {}
    #     for s in stage:
    #         l_r = []
    #         l_g = []
    #         l_b = []
    #         color_lower = np.array([0, 0, 0])
    #         color_upper = np.array([255, 255, 255])
    #         count = 0
    #         show_count = 0
    #         while True:
    #             self.check_quit()
    #             ret, frame = self.cap.read()
    #             b, g, r = cv2.split(frame)
    #             if self.button.press_d() and count < 10:
    #                 m_r = int(np.mean(r[(160 - 3 * count):(175 - 3 * count), 160:175]))
    #                 m_g = int(np.mean(g[(160 - 3 * count):(175 - 3 * count), 160:175]))
    #                 m_b = int(np.mean(b[(160 - 3 * count):(175 - 3 * count), 160:175]))
    #                 print(m_r, m_g, m_b)
    #                 l_r.append(m_r)
    #                 l_g.append(m_g)
    #                 l_b.append(m_b)
    #                 count += 1
    #             if count == 10:
    #                 color_upper = [min(max(l_r) + 25, 255), min(max(l_g) + 25, 255), min(max(l_b) + 25, 255)]
    #                 color_lower = [max(min(l_r) - 15, 0), max(min(l_g) - 15, 0), max(min(l_b) - 15, 0)]
    #                 color_mask[s] = [color_upper, color_lower]
    #                 color_upper = np.array([max(l_r) + 25, max(l_g) + 25, max(l_b) + 25])
    #                 color_lower = np.array([min(l_r) - 11, min(l_g) - 11, min(l_b) - 11])
    #                 show_count += 1
    #                 if show_count >= 100:
    #                     break
    #             frame = cv2.merge((r, g, b))
    #             mask = cv2.inRange(frame, color_lower, color_upper)
    #             img = cv2.bitwise_and(frame, frame, mask=mask)
    #             cv2.rectangle(img, (160, 160 - 3 * count), (175, 175 - 3 * count), (255, 255, 255), 2)
    #             img = cv2.flip(img, 1)
    #             cv2.putText(img, s + ' ' + str(count) + '/10', (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255),
    #                         2)
    #             cv2.putText(img, 'press D(up right)', (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    #             self.show_img(img)
    #     with open(path, 'w', encoding='utf-8') as f:
    #         json.dump(color_mask, f)
    #     cv2.destroyAllWindows()
    #     sys.exit()
