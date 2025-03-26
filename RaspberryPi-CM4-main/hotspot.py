from demos.uiutils import *
import string
import socket


sys.path.append("..")
button = Button()
# Font Loading
font1 = ImageFont.truetype("/home/pi/model/msyh.ttc", 20)
# Pic Loading
fm_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/wifi@2x.png")
re_logo = Image.open("/home/pi/RaspberryPi-CM4-main/pics/redian@2x.png")

#Color Loading
splash_theme_color = (15, 21, 46)
purple = (24, 47, 223)
draw.rectangle([(0, 0), (320, 240)], fill=splash_theme_color)

'''
    Generate Randomized Wifi Ssid
'''
def generate_wifi_ssid():
    prefix = "xgo-"
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return prefix + suffix

'''
    Generate Randomized Wifi Password
'''
def generate_wifi_password():
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))

'''
    Lcd_Text
'''
def lcd_text(x, y, content):
    draw.text((x, y), content, fill="WHITE", font=font1)

'''
    Get Hotspot IP
'''
def get_ip(ifname):
    import socket, struct, fcntl

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(), 0x8915, struct.pack("256s", bytes(ifname[:15], "utf-8"))
        )[20:24]
    )


ssid = generate_wifi_ssid()
password = generate_wifi_password()


hotspot_cmd = "sudo nmcli device wifi hotspot ssid {} password {}".format(
    ssid, password
)

# Activate wlan0
os.system("sudo ifconfig wlan0 up")
time.sleep(2)

# Disconnect the current connection on wlan0
os.system("sudo nmcli device disconnect wlan0")

# Restart NetworkManager 
os.system("sudo systemctl restart NetworkManager")
time.sleep(5)

# Cleaning up possible residual network connections
os.system("sudo nmcli connection delete Hotspot-7")

# Creat Wifi Hotspot
result = os.system(hotspot_cmd)
if result == 0:
    print("Wi-Fi Hotspot Created Successfully！")
else:
    print("Wi-Fi Hotspot Created Failed，Check The Relevant Settings")


lcd_text(77, 115, "SSID:" + ssid)
lcd_text(77, 150, "PWD:" + password)
splash.paste(fm_logo, (77, 188), fm_logo)
splash.paste(re_logo, (115, 15), re_logo)
ip_address = get_ip("wlan0")
lcd_text(102, 185, ip_address)
display.ShowImage(splash)

while True:
    if  button.press_b():
        time.sleep(1)
        os.system("sudo nmcli connection dowm Hostspot-7")
        print('Hotspot Stopped,Rebooting..')
        time.sleep(1)
        os.system("sudo reboot")
        break

