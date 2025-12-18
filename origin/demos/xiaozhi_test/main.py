import argparse
import time
import logging
import sys
import signal
import subprocess  # 新增
from src.application import Application
from src.utils.logging_config import get_logger
from src.key import language
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch
splash_theme_color = (15, 21, 46)
la=language()

#version=2.0

# Display Init
display = LCD_2inch.LCD_2inch()
display.clear()
if la=="cn":
  background_image_path = "/home/jinliang/RaspberryPi-CM4-main/demos/xiaozhi_test/src/xiaozhi_cn.png"  # 替换为你的图片路径
else:
  background_image_path = "/home/jinliang/RaspberryPi-CM4-main/demos/xiaozhi_test/src/xiaozhi_en.png"  # 替换为你的图片路径

splash = Image.open(background_image_path)
draw = ImageDraw.Draw(splash)
text_color = (255, 255, 255)
color = (102, 178, 255)
gray_color = (128, 128, 128)
rectangle_x = (display.width - 120) // 2  
rectangle_y = 50  
rectangle_width = 200
rectangle_height = 30
draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height), fill=color)
font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 16)
if la=="cn":
  draw.text((rectangle_x + 70, rectangle_y + 5), '启动中...', fill=text_color, font=font2)
else:
  draw.text((rectangle_x + 50, rectangle_y + 5), 'Starting up...', fill=text_color, font=font2)
display.ShowImage(splash)

logger = get_logger(__name__)
'''
def kill_pulseaudio():
    """关闭 PulseAudio 服务"""
    try:
        subprocess.run(["pulseaudio", "--kill"], check=True)
        logger.info("已关闭 PulseAudio")
    except subprocess.CalledProcessError as e:
        logger.warning(f"关闭 PulseAudio 失败: {e}")
'''
def kill_pulseaudio():
    try:
        result = subprocess.run(["pgrep", "-x", "pulseaudio"], capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                subprocess.run(["pulseaudio", "--kill"], check=True, timeout=5)
                logger.info("已正常关闭 PulseAudio")
            except subprocess.TimeoutExpired:
                subprocess.run(["pkill", "-9", "-x", "pulseaudio"])
                logger.warning("强制终止 PulseAudio")
            except Exception as e:
                logger.warning(f"关闭 PulseAudio 时出错: {e}")
                return False
            
            time.sleep(1)
            check_result = subprocess.run(["pgrep", "-x", "pulseaudio"], stdout=subprocess.DEVNULL)
            if check_result.returncode == 0:
                logger.error("PulseAudio 仍然在运行")
                return False
            
            return True
        else:
            logger.info("PulseAudio 没有运行")
            return True
            
    except Exception as e:
        logger.error(f"检查/关闭 PulseAudio 时发生异常: {e}")
        return False
'''
def start_pulseaudio():
    """启动 PulseAudio 服务"""
    try:
        subprocess.run(["pulseaudio", "--start"], check=True)
        logger.info("已启动 PulseAudio")
    except subprocess.CalledProcessError as e:
        logger.warning(f"启动 PulseAudio 失败: {e}")
'''
def start_pulseaudio():
    try:
        # 先尝试正常关闭
        subprocess.run(["pulseaudio", "--kill"], check=True)
        time.sleep(1)  # 等待释放资源
        
        # 检查是否真的关闭
        result = subprocess.run(["pgrep", "-x", "pulseaudio"], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            subprocess.run(["pkill", "-9", "-x", "pulseaudio"])  # 强制关闭
        
        # 重新启动 PulseAudio
        subprocess.run(["pulseaudio", "--start"], check=True)
        time.sleep(2)  # 等待 PulseAudio 完全启动
        return True
    except Exception as e:
        print(f"重启 PulseAudio 失败: {e}")
        return False

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    logger.info("接收到中断信号，正在关闭...")
    app = Application.get_instance()
    app.shutdown()
    start_pulseaudio()  # 退出时恢复 PulseAudio
    sys.exit(0)

def main():
    """程序入口点"""
    signal.signal(signal.SIGINT, signal_handler)
    kill_pulseaudio()  # 启动时关闭 PulseAudio

    try:
        app = Application.get_instance()
        logger.info("应用程序已启动，按 Ctrl+C 退出")
        app.run()
    except Exception as e:
        logger.error(f"程序发生错误: {e}", exc_info=True)
        start_pulseaudio()  # 出错时恢复 PulseAudio
        return 1
    finally:
        start_pulseaudio()  # 确保无论如何都恢复 PulseAudio

    return 0

if __name__ == "__main__":
    sys.exit(main())
