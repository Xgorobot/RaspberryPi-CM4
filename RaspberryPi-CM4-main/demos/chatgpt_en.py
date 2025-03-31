from gpt_utils import *

# ------------------------------------------------------------------
quitmark = 0


import threading
def action(num):
    global quitmark
    while quitmark == 0:
        time.sleep(0.01)
        if button.press_b():
            print("quit!!!!!!!!!!!!!!!!!!!!!!!!!")
            quitmark = 1
            os._exit(0)


check_button = threading.Thread(target=action, args=(0,))
check_button.start()

import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    while 1:
        play_anmi = True
        start_audio()
        if quitmark == 0:
            xunfei = ""
            try:
                speech_text = SpeechRecognition()
            except:
                speech_text = ""
            if speech_text != "":
                speech_list = line_break(speech_text)
                print(speech_list)
                lcd_draw_string(
                    draw,
                    10,
                    111,
                    speech_list,
                    color=(255, 255, 255),
                    scale=font2,
                    mono_space=False,
                )
                display.ShowImage(splash)
                lines = len(speech_list.split("\n"))
                tick = 0.3
                if lines > 6:
                    scroll_text_on_lcd(re_e, 10, 111, 6, tick)
                time.sleep(2.5)
                lcd_rect(0, 0, 320, 240, splash_theme_color, -1)
                display.ShowImage(splash)
                re = gpt(speech_text)
                re_e = line_break(re)
                print(re_e)
                lcd_rect(0, 110, 320, 240, splash_theme_color, -1)
                display.ShowImage(splash)
                lcd_draw_string(
                    draw,
                    10,
                    111,
                    re_e,
                    color=(255, 255, 255),
                    scale=font2,
                    mono_space=False,
                )
                display.ShowImage(splash)
                lines = len(re_e.split("\n"))
                tick = 0.3
                if lines > 6:
                    scroll_text_on_lcd(re_e, 10, 111, 6, tick)
                tts(re)
                lcd_rect(0, 0, 320, 240, splash_theme_color, -1)
                display.ShowImage(splash)

        if quitmark == 1:
            print("main quit")
            break

else:
    draw_offline()
    while 1:
        if button.press_b():
            break
