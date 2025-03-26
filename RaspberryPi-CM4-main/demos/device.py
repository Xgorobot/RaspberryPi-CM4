from uiutils import *

sys.path.append("..")

#Language Loading
la = load_language()
#Init Key
button = Button()

'''
    LCD_Text
'''
def lcd_text(x, y, content):
    draw.text((x, y), content, fill="WHITE", font=font1)
    display.ShowImage(splash)

'''
    LCD_Text_Title
'''
def lcd_text_title(x, y, content):
    draw.text((x, y), content, fill="WHITE", font=font2)
    display.ShowImage(splash)

#Pic Loading
fm_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/F@2x.png")
py_wave = Image.open("/home/pi/RaspberryPi-CM4-main/pics/P@2x.png")
os_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/os@2x.png")

#Version Information
fm1 = dog.read_firmware()
fm2 = dog.read_lib_version()
fm3 = "D-CM4"

#Color Define
splash_theme_color = (15, 21, 46)
purple = (24, 47, 223)

draw.rectangle([(20, 90), (100, 210)], fill=splash_theme_color)
draw.rectangle([(120, 90), (200, 210)], fill=splash_theme_color)
draw.rectangle([(220, 90), (300, 210)], fill=splash_theme_color)

splash.paste(fm_logo, (40, 70), fm_logo)
splash.paste(py_wave, (140, 70), py_wave)
splash.paste(os_logo, (240, 70), os_logo)

text_width = draw.textlength(la["DEVICE"]["DEVICEINFO"], font=font2)
title_x = (320 - text_width) / 2
lcd_text_title(title_x, 20, la["DEVICE"]["DEVICEINFO"])
lcd_text(25, 115, "Firmware")
lcd_text_title(26, 160, fm1)
lcd_text(133, 115, "Python")
lcd_text_title(135, 160, fm2)
lcd_text(250, 115, "OS")
lcd_text_title(240, 160, fm3)

while True:
    time.sleep(0.01)
    if button.press_a():
        break
    elif button.press_b():
        os._exit(0)
