from gpt_utils import *


def actions(act):
    commandlist = [
        "Go forward",
        "Go back",
        "Turn left",
        "Turn right",
        "Left translation",
        "Right translation",
        "Dance",
        "Push up",
        "Take a pee",
        "Sit down",
        "Wave hand",
        "Stretch",
        "Hand shake",
        "Pray",
        "Looking for food",
        "Chicken head",
    ]
    mincmd = 0
    minindex = len(commandlist)
    mark = False
    acts = 0
    for i, cmd in enumerate(commandlist):
        ix = act.find(cmd)
        if ix > -1 and ix <= minindex:
            mincmd = i + 1
            minindex = ix
            mark = True
            acts = 1
    if mark:
        if mincmd == 1:
            dog.move_x(12)
            time.sleep(3)
            dog.reset()
        elif mincmd == 2:
            dog.move_x(-12)
            time.sleep(3)
            dog.reset()
        elif mincmd == 3:
            dog.turn(60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd == 4:
            dog.turn(-60)
            time.sleep(1.5)
            dog.reset()
        elif mincmd == 5:
            dog.move_y(6)
            time.sleep(3)
            dog.reset()
        elif mincmd == 6:
            dog.move_y(-6)
            time.sleep(3)
            dog.reset()
        elif mincmd == 7:  # dacne
            dog.action(23)
            time.sleep(3)
        elif mincmd == 8:  # Grab
            dog.action(21)
            time.sleep(3)
        elif mincmd == 9:  # take a pee
            dog.action(11)
            time.sleep(3)
        elif mincmd == 10:  # sit down
            dog.action(12)
            time.sleep(3)
        elif mincmd == 11:  # wave hand
            dog.action(13)
            time.sleep(3)
        elif mincmd == 12:  # stretch
            dog.action(14)
            time.sleep(3)
        elif mincmd == 13:
            dog.action(19)
            time.sleep(3)
        elif mincmd == 14:
            dog.action(17)
            time.sleep(3)
        elif mincmd == 15:
            dog.action(18)
            time.sleep(3)
        elif mincmd == 16:
            dog.action(20)
            time.sleep(3)
        time.sleep(3)
    else:
        time.sleep(1)
        print("command not find")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        draw.rectangle((20, 30, 300, 100), splash_theme_color, "white", width=3)
        lcd_draw_string(
            draw,
            35,
            48,
            "Error in command",
            color=(255, 0, 0),
            scale=font3,
            mono_space=False,
        )
        display.ShowImage(splash)
        dog.reset()
        time.sleep(0.5)


def show_words():
    clear_bottom()
    lcd_draw_string(
        draw,
        57,
        110,
        "Please say the following:",
        color=(255, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        130,
        "Go forward|Go back|Turn left|Turn right",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        150,
        "Left translation|Right translation|Dance",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        170,
        "Push up|Take a pee|Sit down|Wave hand",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        190,
        "Stretch|Hand shake|Pray",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    lcd_draw_string(
        draw,
        10,
        210,
        "Looking for food|Chicken head",
        color=(0, 255, 255),
        scale=font2,
        mono_space=False,
    )
    display.ShowImage(splash)


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
        show_words()
        start_audio()
        if quitmark == 0:
            xunfei = ""
            try:
                speech_text = SpeechRecognition()
            except:
                speech_text = ""
            xunfei = speech_text
            clear_bottom()
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
                actions(xunfei)
        if quitmark == 1:
            print("main quit")
            break

else:
    draw_offline()
    while 1:
        if button.press_b():
            break
