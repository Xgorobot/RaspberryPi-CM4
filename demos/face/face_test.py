from eye_mouth_controller import start_speaking, stop_speaking
from openai import OpenAI
from subprocess import Popen
import os
import time
os.environ["http_proxy"] = "http://192.168.57.6:7890"
os.environ["https_proxy"] = "http://192.168.57.6:7890"

def tts(content):
    client = OpenAI()
    speech_file_path = "speech.mp3"
    response = client.audio.speech.create(
    model="tts-1",
    voice="nova",
    input=content
    )
    response.stream_to_file(speech_file_path)
    proc=Popen("mplayer speech.mp3", shell=True)
    time.sleep(0.5)
    thread = start_speaking(content)
    stop_speaking(thread)

tts('Our work to create safe and beneficial AI requires a deep understanding of the potential risks and benefits, as well as careful consideration of the impact.Learn about safety')