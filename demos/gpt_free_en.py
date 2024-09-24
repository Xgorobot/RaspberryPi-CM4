from gpt_utils import *

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


# ------------------------------------------------------------------
def free_anmi(kinds):
    global ani_num
    if kinds == "after":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "after"
        pic_num = 30
    elif kinds == "before":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "before"
        pic_num = 42
    elif kinds == "recog":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "recog"
        pic_num = 90
    elif kinds == "speak1":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak1/"
        pic_num = 74
    elif kinds == "speak2":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak2/"
        pic_num = 53
    elif kinds == "speak3":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak3/"
        pic_num = 86
    elif kinds == "speak4":
        expression_name_cs = "speak"
        pic_path = "./demos/gptfree/speak4/"
        pic_num = 87
    elif kinds == "waiting":
        pic_path = "./demos/gptfree/"
        expression_name_cs = "waiting"
        pic_num = 114

    ani_num += 1
    if ani_num >= pic_num:
        ani_num = 0
    exp = Image.open(pic_path + expression_name_cs + str(ani_num + 1) + ".png")
    display.ShowImage(exp)


def recog_anmi(t):
    global play_anmi
    print("recog_anmi", play_anmi)
    while 1:
        free_anmi("recog")
        time.sleep(0.03)
        if play_anmi == False:
            break


def speak_anmi(t):
    global play_anmi
    rn = random.randint(1, 4)
    while 1:
        if rn == 1:
            free_anmi("speak1")
        elif rn == 2:
            free_anmi("speak2")
        elif rn == 3:
            free_anmi("speak3")
        elif rn == 4:
            free_anmi("speak4")
        time.sleep(0.02)
        if play_anmi == False:
            break


def start_audio(timel=3, save_file="test.wav"):
    global automark, quitmark
    start_threshold = 60000
    end_threshold = 40000
    endlast = 10
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = timel
    WAVE_OUTPUT_FILENAME = save_file

    if automark:
        p = pyaudio.PyAudio()
        stream_a = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        start_luyin = False
        break_luyin = False
        data_list = [0] * endlast
        sum_vol = 0
        audio_stream = AudiostreamSource()
        libpath = "./demos/libnyumaya_premium.so.3.1.0"
        extractor = FeatureExtractor(libpath)
        detector = AudioRecognition(libpath)
        extactor_gain = 1.0
        keywordIdlulu = detector.addModel("./demos/src/lulu_v3.1.907.premium", 0.6)
        bufsize = detector.getInputDataSize()
        audio_stream.start()

        while not break_luyin:
            if not automark:
                break_luyin = True
            if quitmark == 1:
                print("main quit")
                break
            frame = audio_stream.read(bufsize * 2, bufsize * 2)
            if not frame:
                continue
            features = extractor.signalToMel(frame, extactor_gain)
            prediction = detector.runDetection(features)
            if prediction != 0:
                now = datetime.now().strftime("%d.%b %Y %H:%M:%S")
                if prediction == keywordIdlulu:
                    print("lulu detected:" + now)
                os.system(play_command + " ./demos/src/ding.wav")
                break
            data = stream_a.read(CHUNK, exception_on_overflow=False)
            rt_data = np.frombuffer(data, dtype=np.int16)
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
            vol = sum(fft_data) // len(fft_data)
            data_list.pop(0)
            data_list.append(vol)
            print(start_threshold, vol)
            free_anmi("before")
        audio_stream.stop()
        for i in range(0, 10):
            free_anmi("after")
            time.sleep(0.02)
        while not break_luyin:
            if not automark:
                break_luyin = True
            if quitmark == 1:
                print("main quit")
                break
            data = stream_a.read(CHUNK, exception_on_overflow=False)
            rt_data = np.frombuffer(data, dtype=np.int16)
            fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
            fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
            vol = sum(fft_data) // len(fft_data)
            data_list.pop(0)
            data_list.append(vol)
            if vol > start_threshold:
                sum_vol += 1
                if sum_vol == 1:
                    print("start recording")
                    start_luyin = True
            if start_luyin:
                kkk = lambda x: float(x) < end_threshold
                if all([kkk(i) for i in data_list]):
                    break_luyin = True
                    frames = frames[:-5]
            if start_luyin:
                frames.append(data)
            print(start_threshold, vol)
            free_anmi("waiting")
        print("auto end")
    else:
        p = pyaudio.PyAudio()
        print("录音中...")
        lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
        stream_m = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        start_luyin = False
        break_luyin = False
        data_list = [0] * endlast
        sum_vol = 0
        while not break_luyin:
            if automark:
                break
            if quitmark == 1:
                print("main quit")
                break
            if button.press_d():
                lcd_rect(30, 40, 320, 90, splash_theme_color, -1)
                display.ShowImage(splash)
                print("start recording")
                while 1:
                    data = stream_m.read(CHUNK, exception_on_overflow=False)
                    rt_data = np.frombuffer(data, dtype=np.int16)
                    fft_temp_data = fftpack.fft(rt_data, rt_data.size, overwrite_x=True)
                    fft_data = np.abs(fft_temp_data)[0 : fft_temp_data.size // 2 + 1]
                    vol = sum(fft_data) // len(fft_data)
                    data_list.pop(0)
                    data_list.append(vol)
                    frames.append(data)
                    print(start_threshold)
                    print(vol)
                    draw_wave(int(vol / 10000))
                    display.ShowImage(splash)
                    if button.press_d():
                        break_luyin = True
                        frames = frames[:-5]
                        break
                    if automark:
                        break
        time.sleep(0.3)
        print("manual end")

    if quitmark == 0:
        try:
            stream_a.stop_stream()
            stream_a.close()
        except:
            pass
        try:
            stream_m.stop_stream()
            stream_m.close()
        except:
            pass
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()


def gpt(speech_text):
    global play_anmi
    play_anmi = True
    play_wait_anmi1 = threading.Thread(target=recog_anmi, args=(0,))
    play_wait_anmi1.start()
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": speech_text},
        ],
    )
    re = response.choices[0].message.content
    return re


def tts(content):
    global play_anmi
    client = OpenAI()
    speech_file_path = "speech.mp3"
    response = client.audio.speech.create(model="tts-1", voice="nova", input=content)
    response.stream_to_file(speech_file_path)
    play_anmi = False
    time.sleep(0.5)
    proc = Popen("mplayer speech.mp3", shell=True)
    play_anmi = True
    play_wait_anmi = threading.Thread(target=speak_anmi, args=(0,))
    play_wait_anmi.start()
    proc.wait()
    time.sleep(0.5)
    play_anmi = False


ani_num = 0

from subprocess import Popen
import requests

net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except:
    net = False

if net:
    dog = XGO(port="/dev/ttyAMA0", version="xgolite")
    proc = Popen("sudo cpufreq-set -f 1.5GHz", shell=True)
    play_anmi = True
    while 1:
        start_audio()
        if quitmark == 0:
            xunfei = ""
            try:
                speech_text = SpeechRecognition()
            except:
                speech_text = ""
            if speech_text != "":
                print(speech_text)
                re = gpt(speech_text)
                print(re)
                tts(re)

        if quitmark == 1:
            print("main quit")
            break

else:
    draw_offline()
    while 1:
        if button.press_b():
            break

proc = Popen("sudo cpufreq-set -g conservative", shell=True)
