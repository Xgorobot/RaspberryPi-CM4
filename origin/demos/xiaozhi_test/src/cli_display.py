# vis
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch
from xgolib import XGO

dog = XGO(port='/dev/ttyAMA0', version="xgolite")

from src.key import language
la=language()
print(la)
splash_theme_color = (15, 21, 46)
# Display Init
display = LCD_2inch.LCD_2inch()
display.clear()
if la=="cn":
  background_image_path = "/home/jinliang/RaspberryPi-CM4-main/demos/xiaozhi_test/src/xiaozhi_cn.png"  # 替换为你的图片路径
else:
  background_image_path = "/home/jinliang/RaspberryPi-CM4-main/demos/xiaozhi_test/src/xiaozhi_en.png"  # 替换为你的图片路径

splash = Image.open(background_image_path)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)
import os
from src.auto_platform import play_command
def lcd_draw_string(
        splash,
        x,
        y,
        text,
        color=(255, 255, 255),
        font_size=16,
        max_width=220,
        max_lines=5,
        clear_area=False
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



import asyncio
import threading
import time
from typing import Optional, Callable
from PIL import Image, ImageDraw, ImageFont

from src.utils.logging_config import get_logger
from abc import ABC, abstractmethod
from typing import Optional, Callable
import logging



class BaseDisplay(ABC):
    """显示接口的抽象基类"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.volume_controller = None
        # 检查音量控制依赖
        try:
            from src.utils.volume_controller import VolumeController
            if VolumeController.check_dependencies():
                self.volume_controller = VolumeController()
                self.logger.info("音量控制器初始化成功")
                # 读取系统当前音量
            else:
                self.logger.warning("音量控制依赖不满足，将使用默认音量控制")
        except Exception as e:
            self.logger.warning(f"音量控制器初始化失败: {e}，将使用模拟音量控制")

    @abstractmethod
    def set_callbacks(self,
                      press_callback: Optional[Callable] = None,
                      release_callback: Optional[Callable] = None,
                      status_callback: Optional[Callable] = None,
                      text_callback: Optional[Callable] = None,
                      mode_callback: Optional[Callable] = None,
                      auto_callback: Optional[Callable] = None,
                      abort_callback: Optional[Callable] = None,
                      send_text_callback: Optional[Callable] = None):  # 添加打断回调参数
        """设置回调函数"""
        pass


    @abstractmethod
    def update_status(self, status: str):
        """更新状态文本"""
        pass

    @abstractmethod
    def update_text(self, text: str):
        """更新TTS文本"""
        pass




    @abstractmethod
    def start(self):
        """启动显示"""
        pass

    @abstractmethod
    def on_close(self):
        """关闭显示"""
        pass

    @abstractmethod
    def start_button_listener(self):
        """启动按钮监听"""
        pass

    @abstractmethod
    def stop_button_listener(self):
        """停止按钮监听"""
        pass
from src.key import Button
class CliDisplay(BaseDisplay):
    def __init__(self):
        super().__init__()  # 调用父类初始化
        self.splash_theme_color = (15, 21, 46)
        self.button = Button()
        """初始化CLI显示"""
        self.logger = get_logger(__name__)
        self.running = True
        # self.display = VISdisplay()
        # 状态相关
        self.current_status = "未连接"
        self.current_text = "待命"

        # 回调函数
        self.auto_callback = None
        self.status_callback = None
        self.text_callback = None
        self.abort_callback = None
        self.send_text_callback = None
        # 按键状态
        self.is_r_pressed = False

        # 状态缓存
        self.last_status = None
        self.last_text = None

        # 按钮监听

        self.button = Button()
        self.button_polling_interval = 0.1  # 按钮轮询间隔（秒）
        self.button_listener_running = False  # 按钮监听线程运行标志
        self.button_thread = None  # 按钮监听线程
        
        # 为异步操作添加事件循环
        self.loop = asyncio.new_event_loop()

    def set_callbacks(self,
                      press_callback: Optional[Callable] = None,
                      release_callback: Optional[Callable] = None,
                      status_callback: Optional[Callable] = None,
                      text_callback: Optional[Callable] = None,
                      mode_callback: Optional[Callable] = None,
                      auto_callback: Optional[Callable] = None,
                      abort_callback: Optional[Callable] = None,
                      send_text_callback: Optional[Callable] = None):
        """设置回调函数"""
        self.status_callback = status_callback
        self.text_callback = text_callback
        self.auto_callback = auto_callback
        self.abort_callback = abort_callback
        self.send_text_callback = send_text_callback


    def update_status(self, status: str):
        """更新状态文本"""
        if status != self.current_status:
            self.current_status = status
            self._print_current_status()

    def update_text(self, text: str):
        """更新TTS文本"""
        if text != self.current_text:
            self.current_text = text
            self._print_current_status()


    def start_button_listener(self):
        '''启动按钮监听'''
        def button_polling_loop():
            self.button_listener_running = True
            while self.running and self.button_listener_running:
                try:
                    # 检测按钮A：触发auto_callback
                    if self.button.press_a():
                        self.logger.info("右下键被按下,触发自动对话")
                        if self.auto_callback:
                            self.auto_callback()
                    elif self.button.press_b():
                        self.logger.info("左下键被按下，触发退出")
                        dog.reset()
                        self.on_close()  # 直接调用关闭逻辑
                        break  # 退出循环（因self.running会被设为False）
                    elif self.button.press_d():
                        self.logger.info("右上键被按下，打断对话")
                        if self.abort_callback:
                            self.abort_callback()
                except Exception as e:
                    self.logger.error(f"按钮检测错误: {e}")
                time.sleep(self.button_polling_interval)  # 控制轮询频率
            self.button_listener_running = False
            # 启动独立线程
        self.button_thread = threading.Thread(target=button_polling_loop, daemon=True)
        self.button_thread.start()
        self.logger.info("按钮监听器启动成功")

    def stop_button_listener(self):
        '''停止按钮监听'''
        if not self.button_listener_running:
            return
        self.button_listener_running = False  
        self.logger.info("按钮监听器已停止")



    def start(self):

        # 启动状态更新线程
        self.start_update_threads()

        # 启动按钮监听
        self.start_button_listener()

        # 主循环
        try:
            while self.running:
                if self.current_status == '待命':
                    #splash = Image.open(background_image_path)
                    draw = ImageDraw.Draw(splash)
                    text_color = (255, 255, 255)
                    color = (102, 178, 255)
                    gray_color = (128, 128, 128)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 50  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 30
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=color)
                    font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
                    if la=="cn":
                      draw.text((rectangle_x + 70, rectangle_y + 5), '等待唤醒', fill=text_color, font=font2)
                    else:
                      draw.text((rectangle_x + 9, rectangle_y + 5), 'Waiting to be awakened', fill=text_color, font=font2)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 100  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 100
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=gray_color)
                    if la=="cn":
                      text1="请说“你好,lulu”或者手动唤醒"
                    else:
                      text1="Please say 'Hi, Lulu' or  wake up manually."
                    lcd_draw_string(
                    draw,
                    x=70,
                    y=105,
                    text=text1,
                    color=(255, 255, 255),
                    font_size=16,
                    max_width=190,
                    max_lines=5,
                    clear_area=False
                    )
                    display.ShowImage(splash)
                elif self.current_status == '说话中...':
                    #splash = Image.open(background_image_path)
                    draw = ImageDraw.Draw(splash)
                    text_color = (255, 255, 255)
                    color = (153, 205, 153)
                    gray_color = (128, 128, 128)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 50  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 30
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=color)
                    font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
                    if la=="cn":
                      draw.text((rectangle_x + 80, rectangle_y + 5), "说话中", fill=text_color, font=font2)
                    else:
                      draw.text((rectangle_x + 60, rectangle_y + 5), "In speaking", fill=text_color, font=font2)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 100  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 100
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=gray_color)
                    content = f"{self.current_text}"
                    lcd_draw_string(
                    draw,
                    x=70,
                    y=105,
                    text= content,
                    color=(255, 255, 255),
                    font_size=16,
                    max_width=190,
                    max_lines=5,
                    clear_area=False
                    )
                    display.ShowImage(splash)
                elif self.current_status == '连接中...':
                    #splash = Image.open(background_image_path)
                    draw = ImageDraw.Draw(splash)
                    text_color = (255, 255, 255)
                    color = (255, 102, 102)
                    gray_color = (128, 128, 128)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 50  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 30
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=color)
                    font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
                    if la=="cn":
                      draw.text((rectangle_x + 80, rectangle_y + 5), "连接中", fill=text_color, font=font2)
                    else:
                      draw.text((rectangle_x + 65, rectangle_y + 5), "Connecting", fill=text_color, font=font2)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 100  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 100
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=gray_color)
                    if la=="cn":
                      text2="正在连接云端服务器"
                    else:
                      text2="Connecting to the cloud server"
                    lcd_draw_string(
                    draw,
                    x=70,
                    y=105,
                    text=text2,
                    color=(255, 255, 255),
                    font_size=16,
                    max_width=190,
                    max_lines=5,
                    clear_area=False
                    )
                    display.ShowImage(splash)
                if self.current_status == '聆听中...':
                    #splash = Image.open(background_image_path)
                    draw = ImageDraw.Draw(splash)
                    text_color = (255, 255, 255)
                    color = (255, 215, 0)
                    gray_color = (128, 128, 128)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 50  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 30
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=color)
                    font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
                    if la=="cn":
                      draw.text((rectangle_x + 80, rectangle_y + 5), "聆听中", fill=text_color, font=font2)
                    else:
                      draw.text((rectangle_x + 70, rectangle_y + 5), "Listening", fill=text_color, font=font2)
                    rectangle_x = (display.width - 120) // 2  # 矩形条居中的x坐标
                    rectangle_y = 100  # 矩形条y坐标
                    rectangle_width = 200
                    rectangle_height = 100
                    draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=gray_color)
                    if la=="cn":
                      text3="聆听中,请说话"
                    else:
                      text3="If Xiaozhi doesn't answer in English, you can tell  him to speak English."
                    lcd_draw_string(
                    draw,
                    x=70,
                    y=105,
                    text=text3,
                    color=(255, 255, 255),
                    font_size=16,
                    max_width=190,
                    max_lines=5,
                    clear_area=False
                    )
                    display.ShowImage(splash)
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.on_close()

    def on_close(self):
        """关闭CLI显示"""
        self.running = False
        print("\n正在关闭应用...")
        self.stop_button_listener()

    def _button_listener(self):
        """按钮监听线程"""
        
        try:
            while self.running:
                if self.button.press_b():
                    dog = XGO(port='/dev/ttyAMA0', version="xgolite")
                    self.on_close()
                    break
                elif self.button.press_a():
                    if self.auto_callback:
                        self.auto_callback()
                elif self.button.press_d():
                    if self.abort_callback:
                        self.abort_callback()
                else:
                    if self.send_text_callback:
                        # 获取应用程序的事件循环并在其中运行协程
                        from src.application import Application
                        app = Application.get_instance()
                        if app and app.loop:
                            asyncio.run_coroutine_threadsafe(
                                self.send_text_callback(cmd),
                                app.loop
                            )
                        else:
                            print("应用程序实例或事件循环不可用")
        except Exception as e:
            self.logger.error(f"按钮监听错误: {e}")

    def start_update_threads(self):
        """启动更新线程"""
        def update_loop():
            while self.running:
                try:
                    # 更新状态
                    if self.status_callback:
                        status = self.status_callback()
                        if status and status != self.current_status:
                            self.update_status(status)

                    # 更新文本
                    if self.text_callback:
                        text = self.text_callback()
                        if text and text != self.current_text:
                            self.update_text(text)


                except Exception as e:
                    self.logger.error(f"状态更新错误: {e}")
                time.sleep(0.1)

        # 启动更新线程
        threading.Thread(target=update_loop, daemon=True).start()

    def _print_current_status(self):
        """打印当前状态"""
        # 检查是否有状态变化
        status_changed = (
            self.current_text != self.last_text 
        )
        status_changed_status = (
            self.current_status != self.last_status
        )
        if status_changed_status and self.current_status == '聆听中...':
            os.system(play_command + " /home/jinliang/RaspberryPi-CM4-main/ding.wav")


        if status_changed:
            print("\n=== 当前状态 ===")
            print(f"状态: {self.current_status}")
            print(f"文本: {self.current_text}")
            print("===============\n")

            # 更新缓存
            self.last_status = self.current_status
            self.last_text = self.current_text