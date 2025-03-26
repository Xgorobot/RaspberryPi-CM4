#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json,random,sys,os
import time
import requests
import paho.mqtt.client as mqtt
import threading
import pyaudio
import opuslib 
import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
import logging
from gpiozero import Button
import spidev as SPI
from PIL import Image, ImageDraw, ImageFont
import xgoscreen.LCD_2inch as LCD_2inch
splash_theme_color = (15, 21, 46)

# Display Init
display = LCD_2inch.LCD_2inch()
display.Init()
display.clear()

# Init Splash
splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
draw = ImageDraw.Draw(splash)
display.ShowImage(splash)

OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
MAC_ADDR = 'e4:5f:01:e5:3c:2b'

mqtt_info = {}
aes_opus_info = {"type": "hello", "version": 3, "transport": "udp",
                 "udp": {"server": "120.24.160.13", "port": 8884, "encryption": "aes-128-ctr",
                         "key": "263094c3aa28cb42f3965a1020cb21a7", "nonce": "01000000ccba9720b4bc268100000000"},
                 "audio_params": {"format": "opus", "sample_rate": 24000, "channels": 1, "frame_duration": 60},
                 "session_id": "b23ebfe9"}

iot_msg = {"session_id": "635aa42d", "type": "iot",
           "descriptors": [{"name": "Speaker", "description": "当前 AI 机器人的扬声器",
                            "properties": {"volume": {"description": "当前音量值", "type": "number"}},
                            "methods": {"SetVolume": {"description": "设置音量",
                                                      "parameters": {
                                                          "volume": {"description": "0到100之间的整数", "type": "number"}
                                                      }
                                                      }
                                        }
                            },
                           {"name": "Lamp", "description": "一个测试用的灯",
                            "properties": {"power": {"description": "灯是否打开", "type": "boolean"}},
                            "methods": {"TurnOn": {"description": "打开灯", "parameters": {}},
                                        "TurnOff": {"description": "关闭灯", "parameters": {}}
                                        }
                            }
                           ]
           }

iot_status_msg = {"session_id": "635aa42d", "type": "iot", "states": [
    {"name": "Speaker", "state": {"volume": 50}}, {"name": "Lamp", "state": {"power": False}}]}

goodbye_msg = {"session_id": "b23ebfe9", "type": "goodbye"}
local_sequence = 0
listen_state = None
tts_state = None
key_state = None
audio = None
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
conn_state = False
recv_audio_thread = threading.Thread()
send_audio_thread = threading.Thread()

mqttc = None
ani_num = 0
play_anmi =False
quitmark = False
tts_thread = None
record_thread = None
animation_thread = None

def get_ota_version():
    global mqtt_info
    header = {
        'Device-Id': MAC_ADDR,
        'Content-Type': 'application/json'
    }
    post_data = {"flash_size": 16777216, "minimum_free_heap_size": 8318916, "mac_address": f"{MAC_ADDR}",
                 "chip_model_name": "esp32s3", "chip_info": {"model": 9, "cores": 2, "revision": 2, "features": 18},
                 "application": {"name": "xiaozhi", "version": "0.9.9", "compile_time": "Jan 22 2025T20:40:23Z",
                                 "idf_version": "v5.3.2-dirty",
                                 "elf_sha256": "22986216df095587c42f8aeb06b239781c68ad8df80321e260556da7fcf5f522"},
                 "partition_table": [{"label": "nvs", "type": 1, "subtype": 2, "address": 36864, "size": 16384},
                                     {"label": "otadata", "type": 1, "subtype": 0, "address": 53248, "size": 8192},
                                     {"label": "phy_init", "type": 1, "subtype": 1, "address": 61440, "size": 4096},
                                     {"label": "model", "type": 1, "subtype": 130, "address": 65536, "size": 983040},
                                     {"label": "storage", "type": 1, "subtype": 130, "address": 1048576,
                                      "size": 1048576},
                                     {"label": "factory", "type": 0, "subtype": 0, "address": 2097152, "size": 4194304},
                                     {"label": "ota_0", "type": 0, "subtype": 16, "address": 6291456, "size": 4194304},
                                     {"label": "ota_1", "type": 0, "subtype": 17, "address": 10485760,
                                      "size": 4194304}],
                 "ota": {"label": "factory"},
                 "board": {"type": "bread-compact-wifi", "ssid": "XGO2", "rssi": -58, "channel": 6,
                           "ip": "192.168.66.134", "mac": "e4:5f:01:e5:3c:2b"}}

    response = requests.post(OTA_VERSION_URL, headers=header, data=json.dumps(post_data))
    print(response.text)
    logging.info(f"get version: {response}")
    mqtt_info = response.json()['mqtt']

def aes_ctr_encrypt(key, nonce, plaintext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()

def aes_ctr_decrypt(key, nonce, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext

def send_audio():
    global aes_opus_info, udp_socket, local_sequence, listen_state, audio
    
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    server_ip = aes_opus_info['udp']['server']
    server_port = aes_opus_info['udp']['port']

    if audio is None:
        print("Error: PyAudio (audio) is not initialized!")
        return

    try:
        mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
        
        if mic is None:
            print("Error: Failed to open microphone stream!")
            return

        encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)

        while True:
            if listen_state == "stop":
                time.sleep(0.1)
                continue
            
            data = mic.read(960, exception_on_overflow=False) 
            
            encoded_data = encoder.encode(data, 960)
            
            local_sequence += 1
            new_nonce = nonce[0:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(local_sequence, '08x')

            encrypt_encoded_data = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(new_nonce), bytes(encoded_data))
            data = bytes.fromhex(new_nonce) + encrypt_encoded_data

            udp_socket.sendto(data, (server_ip, server_port))

    except Exception as e:
        print(f"send_audio() error: {e}")

    finally:
        print("Closing microphone stream")
        if 'mic' in locals() and mic is not None: 
            mic.stop_stream()
            mic.close()

def recv_audio():
    global aes_opus_info, udp_socket, audio
    
    if udp_socket is None:
        print("Warning: udp_socket was None! Reinitializing...")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    sample_rate = aes_opus_info['audio_params']['sample_rate']
    frame_duration = aes_opus_info['audio_params']['frame_duration']
    frame_num = int(frame_duration / (1000 / sample_rate))
    print(f"recv audio: sample_rate -> {sample_rate}, frame_duration -> {frame_duration}, frame_num -> {frame_num}")
    
    decoder = opuslib.Decoder(sample_rate, 1)
    spk = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True, frames_per_buffer=frame_num)
    try:
        while True:
            data, server = udp_socket.recvfrom(4096)

            encrypt_encoded_data = data

            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:16]

            split_encrypt_encoded_data = encrypt_encoded_data[16:]
            decrypt_data = aes_ctr_decrypt(bytes.fromhex(key),
                                           split_encrypt_encoded_data_nonce,
                                           split_encrypt_encoded_data)

            spk.write(decoder.decode(decrypt_data, frame_num))

    except Exception as e:
        print(f"recv audio err: {e}")
    finally:
        udp_socket = None
        spk.stop_stream()
        spk.close()

def free_anmi(kinds):
    global ani_num,quitmark
    if kinds == "after":
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/"
        expression_name_cs = "after"
        pic_num = 30
    elif kinds == "before":
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/"
        expression_name_cs = "before"
        pic_num = 42
    elif kinds == "recog":
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/"
        expression_name_cs = "recog"
        pic_num = 90
    elif kinds == "speak1":
        expression_name_cs = "speak"
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/speak1/"
        pic_num = 74
    elif kinds == "speak2":
        expression_name_cs = "speak"
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/speak2/"
        pic_num = 53
    elif kinds == "speak3":
        expression_name_cs = "speak"
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/speak3/"
        pic_num = 86
    elif kinds == "speak4":
        expression_name_cs = "speak"
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/speak4/"
        pic_num = 87
    elif kinds == "waiting":
        pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/"
        expression_name_cs = "waiting"
        pic_num = 114

    ani_num += 1
    if ani_num >= pic_num:
        ani_num = 0
    exp = Image.open(pic_path + expression_name_cs + str(ani_num + 1) + ".png")
    display.ShowImage(exp)
    
def preload_speak_images():
    global speak_images
    speak_images = {
        "speak1": [],
        "speak2": [],
        "speak3": [],
        "speak4": []
    }
    for kind in speak_images.keys():
        path = f"/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/{kind}/"
        for i in range(1, 300):
            try:
                img = Image.open(f"{path}{kind}{i}.png")
                speak_images[kind].append(img)
            except FileNotFoundError:
                break

def speak_anmi():
    global play_anmi
    print("speak_anmi started")

    last_time = time.perf_counter()
    frame_duration = 0.5

    while play_anmi:
        kind = random.choice(["speak1", "speak2", "speak3", "speak4"])
        images = speak_images.get(kind, [])

        if not images:
            print(f"警告：{kind} 动画未加载")
            continue

        for img in images:
            if not play_anmi:
                break
            current_time = time.perf_counter()
            elapsed = current_time - last_time

            if elapsed >= frame_duration:
                display.ShowImage(img)
                last_time = current_time

            time.sleep(0.005)

    print("speak_anmi stopped")


def start_tts_anmi():
    global play_anmi, tts_thread

    if tts_thread and tts_thread.is_alive():
        return 

    play_anmi = True 
    tts_thread = threading.Thread(target=speak_anmi, daemon=True)
    tts_thread.start()

def stop_tts_anmi():
    global play_anmi
    play_anmi = False 

def on_message(client, userdata, message):
    global aes_opus_info, udp_socket, tts_state, recv_audio_thread, send_audio_thread

    msg = json.loads(message.payload)
    print(f" Received MQTT message: {msg}") 

    if msg['type'] == 'hello':
        aes_opus_info = msg
        print("Setting up UDP connection...")

        try:
            if udp_socket is None:
                udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.connect((msg['udp']['server'], msg['udp']['port']))
            print(f" UDP connected to {msg['udp']['server']}:{msg['udp']['port']}")
        except Exception as e:
            print(f" Error: Failed to connect UDP: {e}")
            return

        if not recv_audio_thread.is_alive():
            print("Starting recv_audio_thread...")
            recv_audio_thread = threading.Thread(target=recv_audio, daemon=True)
            recv_audio_thread.start()
        else:
            print("recv_audio_thread is already running.")

        if not send_audio_thread.is_alive():
            print(" Starting send_audio_thread...")
            send_audio_thread = threading.Thread(target=send_audio, daemon=True)
            send_audio_thread.start()
        else:
            print(" send_audio_thread is already running.")

    elif msg['type'] == 'tts':
        tts_state = msg['state']
        if tts_state == "start":
            print(" TTS started - Showing animation")
            start_tts_anmi()
        elif tts_state == "stop":
            print(" TTS stopped - Hiding animation")
            stop_tts_anmi()

    elif msg['type'] == 'goodbye':
        if udp_socket and aes_opus_info.get('session_id') == msg['session_id']:
            print(" Received goodbye message, closing session.")
            aes_opus_info['session_id'] = None

def on_connect(client, userdata, flags, rs, pr):
    subscribe_topic = mqtt_info['subscribe_topic'].split("/")[0] + '/p2p/GID_test@@@' + MAC_ADDR.replace(':', '_')
    print(f"subscribe topic: {subscribe_topic}")
    client.subscribe(subscribe_topic)

def push_mqtt_msg(message):
    global mqtt_info, mqttc
    mqttc.publish(mqtt_info['publish_topic'], json.dumps(message))

def test_aes():
    nonce = "0100000030894a57f148f4f900000000"
    key = "f3aed12668b8bc72ba41461d78e91be9"

    plaintext = b"Hello, World!"

    ciphertext = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(nonce), plaintext)
    print(f"Ciphertext: {ciphertext.hex()}")

    decrypted_plaintext = aes_ctr_decrypt(bytes.fromhex(key), bytes.fromhex(nonce), ciphertext)
    print(f"Decrypted plaintext: {decrypted_plaintext}")

def test_audio():
    key = urandom(16) 
    print(f"Key: {key.hex()}")
    nonce = urandom(16) 
    print(f"Nonce: {nonce.hex()}")

    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    decoder = opuslib.Decoder(16000, 1)

    p = pyaudio.PyAudio()

    mic = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
    spk = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True, frames_per_buffer=960)

    try:
        while True:

            data = mic.read(960)

            encoded_data = encoder.encode(data, 960)

            encrypt_encoded_data = nonce + aes_ctr_encrypt(key, nonce, bytes(encoded_data))

            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:len(nonce)]
            split_encrypt_encoded_data = encrypt_encoded_data[len(nonce):]
            decrypt_data = aes_ctr_decrypt(key, split_encrypt_encoded_data_nonce, split_encrypt_encoded_data)

            spk.write(decoder.decode(decrypt_data, 960))

    except KeyboardInterrupt:
        print("停止录制.")
    finally:

        mic.stop_stream()
        mic.close()
        spk.stop_stream()
        spk.close()
        p.terminate()

def animation():
    global play_anmi,quitmark
    print("before", play_anmi)
    while play_anmi:
        free_anmi("before")
        time.sleep(0.08)
    print("animation stopped")

def start_animation():
    global animation_thread, play_anmi

    if animation_thread and animation_thread.is_alive():
        return

    play_anmi = True
    animation_thread = threading.Thread(target=animation, daemon=True)
    animation_thread.start()

def stop_animation():
    global play_anmi
    play_anmi = False
    if animation_thread and animation_thread.is_alive():
        animation_thread.join()
    print('animation stopped')

def preload_images():
    global recog_images
    recog_images = []
    pic_path = "/home/pi/RaspberryPi-CM4-main/demos/xiaozhi/Picture/"
    expression_name_cs = "recog"
    pic_num = 90
    
    for i in range(1, pic_num + 1):
        try:
            img = Image.open(pic_path + expression_name_cs + str(i) + ".png")
            recog_images.append(img)
        except Exception as e:
            print(f"Error loading image {i}: {e}")

def free_anmi_preloaded():
    global ani_num, recog_images, display
    if not recog_images:
        print("Warning: recog_images is empty!")
        return

    ani_num = (ani_num + 1) % len(recog_images)
    display.ShowImage(recog_images[ani_num])

def recog_anmi():
    global play_anmi
    print("recog_anmi started")

    frame_duration = 0.08
    last_time = time.perf_counter() 

    while play_anmi:
        current_time = time.perf_counter()
        elapsed_time = current_time - last_time

        if elapsed_time >= frame_duration:
            free_anmi_preloaded()
            last_time = current_time

        time.sleep(0.05)

    print("recog_anmi stopped")

def init_pyaudio():
    global audio
    audio = pyaudio.PyAudio()
    print("PyAudio initialized.")

def init_display():
    display.clear()
    splash = Image.new("RGB", (display.height, display.width), splash_theme_color)
    display.ShowImage(splash)
    print("LCD initialized.")

def start_record_anmi():
    global play_anmi, record_thread

    if record_thread and record_thread.is_alive():
        return
    time.sleep(1)
    play_anmi = True
    record_thread = threading.Thread(target=recog_anmi, daemon=True)
    record_thread.start()  

def start_record_anmi():
    global play_anmi, record_thread

    if record_thread and record_thread.is_alive():
        return
    stop_animation()
    time.sleep(0.05)
    
    play_anmi = True
    record_thread = threading.Thread(target=recog_anmi, daemon=True)
    record_thread.start()

def stop_record_anmi():
    global play_anmi
    play_anmi = False 

def on_space_key_press():
    global key_state, udp_socket, aes_opus_info, listen_state, conn_state

    if key_state == "press":
        return
    key_state = "press"

    start_record_anmi()
    
    if conn_state is False or aes_opus_info['session_id'] is None:
        conn_state = True
        hello_msg = {"type": "hello", "version": 3, "transport": "udp",
                     "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}
        threading.Thread(target=push_mqtt_msg, args=(hello_msg,), daemon=True).start() 
        print(f"Sent hello message: {hello_msg}")

    if tts_state == "start" or tts_state == "entence_start":
        threading.Thread(target=push_mqtt_msg, args=({"type": "abort"},), daemon=True).start()
        print(f"Sent abort message")

    if aes_opus_info['session_id'] is not None:
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "start", "mode": "manual"}
        threading.Thread(target=push_mqtt_msg, args=(msg,), daemon=True).start() 
        print(f"Sent start listen message: {msg}")

def on_space_key_release():
    global aes_opus_info, key_state
    key_state = "release"
    stop_record_anmi()
    if aes_opus_info['session_id'] is not None:
        msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "stop"}
        print(f"send stop listen message: {msg}")
        push_mqtt_msg(msg)

def exit_program():
    print("Button 23 pressed! Exiting program...")
    global play_anmi
    play_anmi = False
    time.sleep(0.1)
    os._exit(0)
    
def run():
    global mqtt_info, mqttc
    get_ota_version()
    
    mqtt_info_defaults = {
        'client_id': 'default_client',
        'username': 'user',
        'password': 'pass',
        'endpoint': 'localhost',
        'publish_topic': 'test_topic',
        'subscribe_topic': 'test_topic'
    }
    for key, value in mqtt_info_defaults.items():
        if key not in mqtt_info:
            print(f"Warning: {key} not found in mqtt_info. Using default value: {value}") 
            mqtt_info[key] = value
    print("Final MQTT Info:", mqtt_info)
    button = Button(17)
    button.when_pressed = on_space_key_press
    button.when_released = on_space_key_release
    
    button23 = Button(23)
    button23.when_pressed = exit_program 
    mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    mqttc.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                  tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(host=mqtt_info['endpoint'], port=8883)
    mqttc.loop_forever()

if __name__ == "__main__":
    init_display() 
    preload_images()
    preload_speak_images()
    init_pyaudio() 
    start_animation()
    run()
    
    print("Initialization complete. Running program...")
    
