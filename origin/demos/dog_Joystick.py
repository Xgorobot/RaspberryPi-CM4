#!/usr/bin/env python3
# coding=utf-8

import os, struct, sys
from xgolib import XGO
import time
import threading
from uiutils import (
    dog,lcd_draw_string, display, splash, draw,language,
    font2, Button,get_font
)
from PIL import Image, ImageDraw,ImageFont
font1=get_font(16)
button=Button()
splash_theme_color = (15, 21, 46)
la=language()
lianjie_image = Image.open("/home/jinliang/RaspberryPi-CM4-main/pics/lianjie@2x.png") 
weilianjie_image = Image.open("/home/jinliang/RaspberryPi-CM4-main/pics/weilianjie@2x.png")

def clear_bottom():
    draw.rectangle([(0, 111), (320, 240)], fill=splash_theme_color)

def clear_top():
    draw.rectangle([(0, 0), (320, 120)], fill=splash_theme_color)
    
def show_connection_status(connected):
    clear_top()
    
    if connected:
        img = lianjie_image.convert("RGBA")
    else:
        img = weilianjie_image.convert("RGBA")
    
    splash.paste(img, (25, 0), img)
    display.ShowImage(splash)

class XGO_Joystick(object):

    def __init__(self, dog, js_id=0, debug=False):
        self.__debug = debug
        self.__js_id = int(js_id)
        self.__js_isOpen = False
        self.__dog = dog
        self.__step_control = 70
        self.__pace_freq = 2
        self.__height = 105
        self.__ignore_count = 20
        self.__play_ball = 0
        self.__crossing_state = False

        self.__STEP_SCALE_X = 0.25 
        self.__STEP_SCALE_Y = 0.2
        self.__STEP_SCALE_Z = 0.7
        
        self.STATE_OK = 0
        self.STATE_NO_OPEN = 1
        self.STATE_DISCONNECT = 2
        self.STATE_KEY_BREAK = 3
        # Find the joystick device.
        print('Joystick Available devices:')
        # Shows the joystick list of the Controler, for example: /dev/input/js0
        for fn in os.listdir('/dev/input'):
            if fn.startswith('js'):
                print('    /dev/input/%s' % (fn))

        # Open the joystick device.
        try:
            js = '/dev/input/js' + str(self.__js_id)
            self.__jsdev = open(js, 'rb')
            self.__js_isOpen = True
            print('---Opening %s Succeeded---' % js)
            show_connection_status(True)
        except:
            self.__js_isOpen = False
            print('---Failed To Open %s---' % js)
            show_connection_status(False)
        # Defining Functional List
        self.__function_names = {
            # BUTTON FUNCTION
            0x0100 : 'A',
            0x0101 : 'B',
            0x0102 : 'X',
            0x0103 : 'Y',
            0x0104 : 'L1',
            0x0105 : 'R1',
            0x0106 : 'SELECT',
            0x0107 : 'START',
            0x0108 : 'MODE',
            0x0109 : 'BTN_RK1',
            0x010A : 'BTN_RK2',

            # AXIS FUNCTION
            0x0200 : 'RK1_LEFT_RIGHT',
            0x0201 : 'RK1_UP_DOWN',
            0x0202 : 'L2',
            0x0203 : 'RK2_LEFT_RIGHT',
            0x0204 : 'RK2_UP_DOWN',
            0x0205 : 'R2',
            0x0206 : 'WSAD_LEFT_RIGHT',
            0x0207 : 'WSAD_UP_DOWN',
        }

    def __del__(self):
        if self.__js_isOpen:
            self.__jsdev.close()
        if self.__debug:
            print("\n---Joystick DEL---\n")

    # Return joystick state
    def is_Opened(self):
        return self.__js_isOpen
    
    # transform data
    def __my_map(self, x, in_min, in_max, out_min, out_max):
        return (out_max - out_min) * (x - in_min) / (in_max - in_min) + out_min


    def __play_ball_task(self, leg_id):
        motor_id = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43]
        angle_down=[-16, 66, 1, -17, 66, 1, -14, 74, 1, -14, 72, 1]

        if leg_id == 2:
            motor_2 = [21, 22, 23]
            angle_hand = [-15, 51, 2, -13, 33, -1, -15, 64, 3, -19, 59, 0]
            angle_play_2 = [10, 0, 0]
            if self.__play_ball:
                self.__dog.motor_speed(100)
                self.__dog.motor(motor_id, angle_down)
                time.sleep(.3)
            if self.__play_ball:
                self.__dog.motor(motor_id, angle_hand)
                time.sleep(.2)
            if self.__play_ball:
                self.__dog.motor_speed(255)
                time.sleep(.01)
            if self.__play_ball:
                self.__dog.motor(motor_2, angle_play_2)
                time.sleep(.3)
            if self.__play_ball:
                self.__dog.motor(motor_id, angle_hand)
                time.sleep(.3)
            if self.__play_ball:
                self.__dog.motor_speed(100)
                self.__dog.motor(motor_id, angle_down)
                time.sleep(.3)
            if self.__play_ball:
                self.__dog.action(0xff)
        self.__height = 105
        self.__play_ball = 0
    
    # reset DOGZILLA
    def __dog_reset(self):
        self.__play_ball = 0
        self.__dog.reset()
        self.__step_control = 70
        self.__pace_freq = 2
        self.__height = 105
        self.__crossing_state = False

    def __obstacle_crossing(self):
        self.__dog.gait_type("high_walk")
        time.sleep(.01)
        self.__dog.pace("slow")
        time.sleep(.01)
        self.__dog.translation('z', 95)
        time.sleep(.01)
        self.__dog.forward(25)

    # crossing mode handle

    def __crossing_handle(self, name, value):
        if name == 'SELECT':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__dog_reset()
        elif name == 'START':
            if self.__debug:
                print (name, ":", value)
            # Stop the action and restore the original position
            if value == 1:
                self.__dog_reset()
        else:
            pass

    # Control robot
    def __data_processing(self, name, value):
        print(f"Input Event - Name: {name}, Value: {value}")
        if name=="RK1_LEFT_RIGHT":
            value = -value / 32767
            if self.__debug:
                print ("%s : %.3f, %d" % (name, value, self.__step_control))
            fvalue = int(self.__step_control * self.__STEP_SCALE_Y * value)
            self.__dog.move('y', fvalue)
        elif name == 'RK1_UP_DOWN':
            value = -value / 32767
            if self.__debug:
                print ("%s : %.3f, %d" % (name, value, self.__step_control))
            fvalue = int(self.__step_control * self.__STEP_SCALE_X * value)
            self.__dog.move('x', fvalue)
        elif name == 'RK2_UP_DOWN':
            value = -value / 32767
            if self.__debug:
                print ("%s : %.3f, %d" % (name, value, self.__step_control))
            # fvalue = -value * 24
            # self.__dog.attitude('r', fvalue)
            if value == 0:
                self.__dog.turn(0)
            elif value == 1 or value == -1:
                # fvalue = int(self.__step_control * self.__STEP_SCALE_Z * value)
                fvalue = int(self.__my_map(self.__step_control, 0, 100, 20, self.__STEP_SCALE_Z*100))*value
                self.__dog.turn(fvalue)
        elif name == 'RK2_LEFT_RIGHT':
            value = value / 32767
            if self.__debug:
                print ("%s : %.3f" % (name, value))
            fvalue = value * 15
            self.__dog.attitude('p', fvalue)
        
        elif name == 'A':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__height = self.__height - 10
                if self.__height < 75:
                    self.__height = 75
                self.__dog.translation('z', self.__height)
        elif name == 'B':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__dog.attitude('y', -35)
            else:
                self.__dog.attitude('r', 0)
                self.__dog.attitude('y', 0)
        elif name == 'X':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__dog.attitude('y', 35)
            else:
                self.__dog.attitude('r', 0)
                self.__dog.attitude('y', 0)
        elif name == 'Y':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__height = self.__height + 10
                if self.__height > 115:
                    self.__height = 115
                self.__dog.translation('z', self.__height)
        elif name == 'L1':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                # self.__dog.action(3) #  CRAWL
                self.__dog.action(10) #  3 Axis
        elif name == 'R1':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                # self.__dog.action(16) # SWING
                if self.__play_ball == 0:
                    self.__play_ball = 2
                    task_1 = threading.Thread(target=self.__play_ball_task, args=(self.__play_ball,), name="play_ball_task")
                    task_1.setDaemon(True)
                    task_1.start()
        elif name == 'SELECT':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                if not self.__crossing_state:
                    self.__crossing_state = True
                    self.__obstacle_crossing() 
                else:
                    self.__dog_reset()
        elif name == 'START':
            if self.__debug:
                print (name, ":", value)
            #Stop the action and restore the original position
            if value == 1:
                self.__dog_reset()
        elif name == 'MODE':
            if self.__debug:
                print (name, ":", value)
        elif name == 'BTN_RK1':
            if self.__debug:
                print (name, ":", value)
            if value == 1:
                self.__step_control = self.__step_control + 30
                if self.__step_control > 100:
                    self.__step_control = 40
        elif name == 'BTN_RK2':
            if value == 1:
                self.__pace_freq = self.__pace_freq + 1
                if self.__pace_freq > 3:
                    self.__pace_freq = 1
                if self.__pace_freq == 1:
                    self.__dog.pace("slow")
                elif self.__pace_freq == 2:
                    self.__dog.pace("normal")
                elif self.__pace_freq == 3:
                    self.__dog.pace("high")
            if self.__debug:
                print (name, ":", value, self.__pace_freq)
        
        elif name == "L2":
            value = ((value/32767)+1)/2
            if self.__debug:
                print ("%s : %.3f" % (name, value))
            if value == 1:
                # self.__dog.action(17) # PRAY
                self.__dog.action(16)
        elif name == "R2":
            value = ((value/32767)+1)/2
            if self.__debug:
                print ("%s : %.3f" % (name, value))
            if value == 1:
                self.__dog.action(11) 
            
        elif name == 'WSAD_LEFT_RIGHT':
            value = -value / 32767
            if self.__debug:
                print ("%s : %.3f" % (name, value))
            fvalue = (value * self.__step_control * self.__STEP_SCALE_Y)
            self.__dog.move('y', fvalue)
        elif name == 'WSAD_UP_DOWN':
            value = -value / 32767
            if self.__debug:
                print ("%s : %.3f, %d" % (name, value, self.__step_control))
            fvalue = int(value * self.__step_control * self.__STEP_SCALE_X)
            self.__dog.move('x', fvalue)
        else:
            pass

    # Handles events for joystick
    def joystick_handle(self):
        if not self.__js_isOpen:
            # if self.__debug:
            #     print('Failed To Open Joystick')
            show_connection_status(False)
            return self.STATE_NO_OPEN
        try:
            evbuf = self.__jsdev.read(8)
            if evbuf:
                time, value, type, number = struct.unpack('IhBB', evbuf)
                func = type << 8 | number
                name = self.__function_names.get(func)
                # print("evbuf:", time, value, type, number)
                # if self.__debug:
                #     print("func:0x%04X, %s, %d" % (func, name, value))
                if name != None:
                    if self.__crossing_state:
                        self.__crossing_handle(name, value)
                    else:
                        self.__data_processing(name, value)
                else:
                    if self.__ignore_count > 0:
                        self.__ignore_count = self.__ignore_count - 1
                    if self.__debug and self.__ignore_count == 0:
                        print("Key Value Invalid")
            return self.STATE_OK
        except KeyboardInterrupt:
            if self.__debug:
                print('Key Break Joystick')
            return self.STATE_KEY_BREAK
        except:
            self.__js_isOpen = False
            print('---Joystick Disconnected---')
            show_connection_status(False)
            return self.STATE_DISCONNECT

    # reconnect Joystick
    def reconnect(self):
        try:
            js = '/dev/input/js' + str(self.__js_id)
            self.__jsdev = open(js, 'rb')
            self.__js_isOpen = True
            self.__ignore_count = 20
            print('---Opening %s Succeeded---' % js)
            show_connection_status(True)
            return True
        except:
            self.__js_isOpen = False
            # if self.__debug:
            #     print('Failed To Open %s' % js)
            show_connection_status(False)
            return False
            
def show_controller_help():
    clear_bottom()
    
    if la == 'cn':
        text_lines = [
            ("←→↑↓: 移动控制",10,150),
            ("A/Y: 高度调节", 10,170),
            ("X/B: 左右转向", 10,190),
            ("L/R: 动作模式",150,150),
            ("RK1/2: 步幅/速度调整",150,170),
            ("SELECT: 越野模式", 150,190)
        ]
    else:
    
        text_lines = [
            ("←→↑↓: Movement",10,150),
            ("A/Y: Height", 10,170), 
            ("X/B: Turning",10,190),
            ("L/R: Modes", 150,150),
            ("RK1/2:Step/speed ",150, 170),
            ("SELECT:off-road", 150,190)
        ]
    
  
    for text,x,y in text_lines:
        lcd_draw_string(draw, x, y, text, color=(0, 255, 255), scale=font1, mono_space=False)
    
    display.ShowImage(splash)

def button_listener():
    while True:
        if button.press_b():
            print("Button B pressed, exiting...")
            os._exit(0) 
        time.sleep(0.1)


#Start button listening thread
button_thread = threading.Thread(target=button_listener)
button_thread.daemon = True  
button_thread.start()

            
if __name__ == '__main__':
    g_debug = False
    show_controller_help()
    if len(sys.argv) > 1:
        if str(sys.argv[1]) == "debug":
            g_debug = True
    print("debug=", g_debug)

    js = XGO_Joystick(dog, debug=g_debug)
    while True:
        state = js.joystick_handle()
        if state != js.STATE_OK:
            if state == js.STATE_KEY_BREAK:
                break
            time.sleep(1)
            js.reconnect()
    del js
 
