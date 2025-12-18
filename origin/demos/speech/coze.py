import random,os,time,threading,pyaudio,requests,logging
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from xgolib import XGO
from PIL import Image, ImageDraw, ImageFont
from key import Button
from audio_ei import start_recording
from language_recognize import test_one
from coze_agent import model_output
from key import language

#version=2.0

la=language()
SPLASH_COLOR = (15, 21, 46)
FONT_PATH = "/home/jinliang/model/msyh.ttc"
FONT_SIZE = 20
DOG_PORT = '/dev/ttyAMA0'
DOG_VERSION = "xgomini"
TEST_NETWORK_URL = "http://www.baidu.com"

ACTION_MAP = {
    "Dance": (23, 6),
    "Pushups": (21, 8),
    "Pee": (11, 7),
    "Stretch": (14, 10),
    "Pray": (19, 3),
    "Chickenhead": (20, 9),
    "Lookforfood": (17, 4),
    "Grabdownwards": (130, 10),
    "Wave": (15, 6),
    "Beg": (17, 3)
}
from auto_platform import AudiostreamSource

WIFI_OFFLINE_PATH = "/home/jinliang/RaspberryPi-CM4-main/pics/offline.png"
font2 = ImageFont.truetype("/home/jinliang/model/msyh.ttc", 22)
color_white = (255, 255, 255)
mic_purple = (24, 47, 223)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000



class GPTCMD:
    def __init__(self):

        self.display = LCD_2inch.LCD_2inch()
        self.display.Init()
        self.splash_theme_color = (15, 21, 46)
        self.splash = Image.new("RGB", (self.display.height, self.display.width), SPLASH_COLOR)
        self.draw = ImageDraw.Draw(self.splash)
        self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        self.network_available = False
        self.dog = XGO(port=DOG_PORT, version=DOG_VERSION)
        self.dog_init()
        self.button = Button()
        self.audio_stream = None
        self.stream_a = None
        self.p = None
        self.action_id = {'趴下': 1, '站起': 2, '匍匐前进': 3, '转圈': 4, '原地踏步': 5, '蹲起': 6, '沿x转动': 7,
                     '沿y转动': 8, '沿z转动': 9, '三轴转动': 10, '撒尿': 11, '坐下': 12, '招手': 13, '伸懒腰': 14,
                     '波浪运动': 15, '摇摆运动': 16, '求食': 17, '找食物': 18, '握手': 19, '展示机械臂': 20,
                     '俯卧撑': 21, '张望': 22, '跳舞': 23, '调皮': 24, '向上抓取': 128, '向中抓取': 129,
                     '向下抓取': 130}
        self.time_list = [0] * 131
        self.time_list[1:25] = [3, 3, 5, 5, 4, 4, 4, 4, 4, 7, 7, 5, 7, 10, 6, 6, 6, 6, 10, 9, 8, 8, 6, 7]
        self.time_list[128:131] = [10, 10, 10]


        # 启动按键检测线程
        self._start_button_thread()
        try:
            wifi_img = Image.open(WIFI_OFFLINE_PATH)
            self.nowifi_image = Image.new("RGB", wifi_img.size, SPLASH_COLOR)
            self.nowifi_image.paste(wifi_img, (0, 0), wifi_img)  
        except Exception as e:
            print(f"加载图片失败: {e}")
            self.nowifi_image = Image.new("RGB", (100, 100), (255, 0, 0))  
    def visual(self, content):
        mic_logo = Image.open("/home/jinliang/RaspberryPi-CM4-main/pics/mic.png")
        mic_purple = (24, 47, 223)
        splash = Image.new("RGB", (self.display.height, self.display.width), self.splash_theme_color)
        draw = ImageDraw.Draw(splash)
        draw.rectangle([0, 0, self.display.width, self.display.height], fill=(15, 21, 46))
        gray_color = (128, 128, 128)

        def draw_cir(ch):
            if ch > 15:
                ch = 15
            draw.bitmap((145, 40), mic_logo, mic_purple)
            radius = 4
            cy = 60
            centers = [(62, cy), (87, cy), (112, cy), (210, cy), (235, cy), (260, cy)]
            for center in centers:
                random_offset = random.randint(0, ch)
                new_y = center[1] + random_offset
                new_y2 = center[1] - random_offset

                draw.line([center[0], new_y2, center[0], new_y], fill=mic_purple, width=11)

                top_left = (center[0] - radius, new_y - radius)
                bottom_right = (center[0] + radius, new_y + radius)
                draw.ellipse([top_left, bottom_right], fill=mic_purple)
                top_left = (center[0] - radius, new_y2 - radius)
                bottom_right = (center[0] + radius, new_y2 + radius)
                draw.ellipse([top_left, bottom_right], fill=mic_purple)

        def draw_wave(ch):
            if ch > 10:
                ch = 10
            start_x = 40
            start_y = 32
            width, height = 80, 50
            y_center = height // 2
            current_y = y_center
            previous_point = (0 + start_x, y_center + start_y)
            draw.bitmap((145, 40), mic_logo, mic_purple)
            x = 0
            while x < width:
                segment_length = random.randint(7, 25)
                gap_length = random.randint(4, 20)

                for _ in range(segment_length):
                    if x >= width:
                        break
                    amplitude_change = random.randint(-ch, ch)
                    current_y += amplitude_change
                    if current_y < 0:
                        current_y = 0
                    elif current_y > height - 1:
                        current_y = height - 1
                    current_point = (x + start_x, current_y + start_y)
                    draw.line([previous_point, current_point], fill=mic_purple)
                    previous_point = current_point
                    x += 1
                for _ in range(gap_length):
                    if x >= width:
                        break
                    current_point = (x + start_x, y_center + start_y)
                    draw.line([previous_point, current_point], fill=mic_purple, width=2)
                    previous_point = current_point
                    x += 1
            start_x = 210
            start_y = 32
            width, height = 80, 50
            y_center = height // 2
            current_y = y_center
            previous_point = (0 + start_x, y_center + start_y)
            draw.rectangle(
                [(start_x - 1, start_y), (start_x + width, start_y + height)],
                fill=self.splash_theme_color,
            )
            x = 0
            while x < width:
                segment_length = random.randint(7, 25)
                gap_length = random.randint(4, 20)
                for _ in range(segment_length):
                    if x >= width:
                        break
                    amplitude_change = random.randint(-ch, ch)
                    current_y += amplitude_change
                    if current_y < 0:
                        current_y = 0
                    elif current_y > height - 1:
                        current_y = height - 1
                    current_point = (x + start_x, current_y + start_y)
                    draw.line([previous_point, current_point], fill=mic_purple)
                    previous_point = current_point
                    x += 1
                for _ in range(gap_length):
                    if x >= width:
                        break
                    current_point = (x + start_x, y_center + start_y)
                    draw.line([previous_point, current_point], fill=mic_purple, width=2)
                    previous_point = current_point
                    x += 1

        draw_wave(5)
        rectangle_x = (self.display.width - 120) // 2  # 矩形条居中的x坐标
        rectangle_y = 110  # 矩形条y坐标
        rectangle_width = 200
        rectangle_height = 80
        draw.rectangle((rectangle_x, rectangle_y, rectangle_x + rectangle_width, rectangle_y + rectangle_height),
                       fill=gray_color)

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

        lcd_draw_string(
            draw,
            x=70,
            y=115,
            text=content,
            color=(255, 255, 255),
            font_size=16,
            max_width=190,
            max_lines=5,
            clear_area=False
        )
        self.display.ShowImage(splash)

    def dog_init(self):

        fm = self.dog.read_firmware()
        if fm[0] == 'M':
            print('XGO-MINI')
            self.dog = XGO(port='/dev/ttyAMA0', version="xgomini")
            self.dog_type = 'M'
        else:
            self.dog = XGO(port='/dev/ttyAMA0', version="xgolite")
            print('XGO-LITE')
            self.dog_type = 'L'
        if self.dog_type == 'L':
            self.mintime_yaw = 0.8
            self.mintime_x = 0.1
        else:
            self.mintime_yaw = 0.7
            self.mintime_x = 0.3
    def adaptive_move(self, distance):
        if distance < 15:
            speed = 10
        elif distance < 30:
            speed = 15
        else:
            speed = 20
        return speed
    def adaptive_turn(self, yaw):
        if self.dog_type == 'M':
            if yaw < 20:
                turn_speed = 10
            elif yaw < 50:
                turn_speed = 20
            else:
                turn_speed = 30
            return turn_speed
        else:
            turn_speed = 30
            return turn_speed
    def _start_button_thread(self):
        def check_button():
            while True:
                if self.button.press_b():
                    try:
                        self.audio_stream.stop()
                        logging.warning('audio_stream kill')
                    except Exception as e:
                        logging.warning(e)
                    self.dog.reset()
                    try:
                        self.stream_a.stop_stream()
                        self.stream_a.close()
                        logging.warning("stream_a kill")
                    except Exception as e:
                        logging.warning(e)
                    try:
                        self.p.terminate()
                        logging.warning("p terminate")
                    except:
                        pass
                    print("B键按下, 退出程序")
                    os._exit(0)
                time.sleep(0.1)

        thread = threading.Thread(target=check_button, daemon=True)
        thread.start()

    def show_message(self, text, color=(255, 255, 255)):
        self.draw.rectangle((0, 0, self.display.height, self.display.width), fill=SPLASH_COLOR)
        self.draw.text((80, 100), text, fill=color, font=self.font)
        self.display.ShowImage(self.splash)

    def execute_action(self, action_name):
        if action_name in ACTION_MAP:
            action_id, duration = ACTION_MAP[action_name]
            self.dog.action(action_id)
            time.sleep(duration)
            return True
        return False

    def check_network(self):
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            try:
                requests.get(TEST_NETWORK_URL, timeout=1)
                print("Net is connected")
                self.network_available = True
                return True 
            except:
                print(f"Network connection attempt {attempt + 1} failed")
                attempt += 1
                time.sleep(1)
        
        print("Network connection failed after 5 attempts")
        self.network_available = False
        self.draw.rectangle((0, 0, self.display.height, self.display.width), fill=SPLASH_COLOR)
        img_width, img_height = self.nowifi_image.size
        x_pos = (self.display.height - img_width) // 2
        y_pos = 40
        self.splash.paste(self.nowifi_image, (x_pos, y_pos))
        if la == "cn":
            text = "WIFI未连接或无网络"
        else:
            text = "WIFI is not connected"
        text_width = self.draw.textlength(text, font=font2)
        x_position = (self.display.height - text_width) // 2
        self.draw.text((x_position, 170), text, fill=color_white, font=font2)
        self.display.ShowImage(self.splash)
        
        return False

    def run(self):
        if not self.check_network():
            while True:
                time.sleep(1)
            return
            
        if la=="cn":
          self.show_message("正在启动，请稍后", color=(255, 255, 255))
        else:
          self.show_message("Starting up...", color=(255, 255, 255))
        while True:
            # try:
            self.p = pyaudio.PyAudio()
            self.stream_a = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )
            self.audio_stream = AudiostreamSource()
            logging.warning('音频初始化完成')
            start_recording(self.p, self.stream_a, self.audio_stream)
            logging.warning("录音结束")
            if la=="cn":
              self.visual(content="指令识别中，请稍等")
            else:
              self.visual(content="Instruction recognizing...")
            content = test_one()
            logging.warning(f"识别内容: {content}")


            if not content:
                logging.warning("录音出错")
                continue

            action_results = model_output(content=content)
            logging.warning(action_results)
            self.visual(content=content)
            try:
                for i in action_results:
                    print(i[0])
                    if i[0] == 'x' or i[0] == 'y':
                        speed = self.adaptive_move(int(i[1]))
                        self.dog.move(i[0], speed * int(i[1]) / abs(int(i[1])))
                        time.sleep(abs(int(i[1] / speed)))
                        self.dog.stop()
                        time.sleep(0.5)
                    elif i[0] == 'turn':
                        if self.dog_type == 'L':
                            i[1] = 1.5 * int(i[1])
                        turn_speed = self.adaptive_turn(int(i[1]))
                        self.dog.turn(turn_speed * int(i[1]) / abs(int(i[1])))
                        time.sleep(abs(int(i[1] / turn_speed)))
                        self.dog.stop()
                        time.sleep(0.5)
                    elif i[0] == 'action':
                        self.dog.action(int(self.action_id[i[1]]))
                        time.sleep(int(self.time_list[int(self.action_id[i[1]])]))
                        self.dog.stop()
                        time.sleep(0.5)
                    elif i[0] == 'pace':
                        self.dog.pace(i[1])
                        time.sleep(0.2)
                    elif i[0] == 'translation':
                        logging.warning(f'沿着{i[1][0]}轴平移{i[1][1]}')
                        self.dog.translation(i[1][0], i[1][1])
                        time.sleep(1)
                    elif i[0] == 'attitude':
                        logging.warning(f'沿着{i[1][0]}轴旋转{i[1][1]}')
                        self.dog.attitude(i[1][0], i[1][1])
                        time.sleep(1)
                    elif i[0] == 'arm':
                        self.dog.arm(i[1][0], i[1][1])
                        time.sleep(1)
                    elif i[0] == 'claw':
                        self.dog.claw(i[1])
                        time.sleep(1)
                    elif i[0] == 'imu':
                        self.dog.imu(i[1])
                        time.sleep(1)
                    elif i[0] == 'perform':
                        self.dog.perform(i[1])
                        time.sleep(10)
                    elif i[0] == 'reset':
                        self.dog.reset()
                        time.sleep(1)
                    elif i[0] == 'motor':
                        self.dog.motor(i[1][0], i[1][1])
                        time.sleep(1)
                    elif i[0] == 'battery':
                        print(self.dog.read_battery())
                        time.sleep(1)
                    elif i[0] == 'leg':
                        self.dog.leg(i[1][0],i[1][1])
                        time.sleep(1)
                    elif i[0] == '重试':
                        continue
                    elif i[0] == '退出':
                        self.dog.reset()
                        time.sleep(1)
                        print('退出')
                        exit()
                    else:
                        continue
            except Exception as e:
                logging.warning(f'发生未知错误: {e}')
                self.visual(content="指令识别错误，请重试")
                time.sleep(2)
                continue



if __name__ == "__main__":
    controller = GPTCMD()
    controller.run()
