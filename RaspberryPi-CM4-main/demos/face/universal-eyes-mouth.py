import numpy as np
import os
import random
import threading
import time
from PIL import Image
import matplotlib.pyplot as plt

# Load eye images
open_eyes = Image.open('1.png')
closed_eyes = Image.open('2.png')

# Scale eye images
EYE_SCALE_FACTOR = 0.4
open_eyes_scaled = open_eyes.resize((int(open_eyes.width * EYE_SCALE_FACTOR), int(open_eyes.height * EYE_SCALE_FACTOR)), Image.LANCZOS)
closed_eyes_scaled = closed_eyes.resize((int(closed_eyes.width * EYE_SCALE_FACTOR), int(closed_eyes.height * EYE_SCALE_FACTOR)), Image.LANCZOS)

# Last blink time
last_blink_time = time.time()

# Path to mouth images
pic_path = "expression/mouth/"

# Load and scale mouth images
MOUTH_SCALE_FACTOR = 0.5
mouth_images = {}
for i in range(1, 15):
    image_path = os.path.join(pic_path, f"{i}.png")
    image = Image.open(image_path)
    scaled_image = image.resize((int(image.width * MOUTH_SCALE_FACTOR), int(image.height * MOUTH_SCALE_FACTOR)), Image.LANCZOS)
    mouth_images[str(i)] = scaled_image


# Map letters to images
letter_to_mouth = {
    # Mapping for each letter
    'A': '1', 'B': '2', 'C': '3', 'D': '4', 'E': '5',
    'F': '6', 'G': '7', 'H': '8', 'I': '9', 'J': '10',
    'K': '11', 'L': '12', 'M': '13', 'N': '14', 'O': '1',
    'P': '2', 'Q': '3', 'R': '4', 'S': '5', 'T': '6',
    'U': '7', 'V': '8', 'W': '9', 'X': '10', 'Y': '11',
    'Z': '12', 'Ä': '13', 'Ö': '14', 'Ü': '1', 'ß': '2'
}

# Global variables for current word and animation control
current_word = ""  
animate_mouth = True

def show_mouth_animation():
    global last_blink_time, current_word, animate_mouth
    plt.ion()  # Turn on interactive mode for live updates
    fig, ax = plt.subplots()
    
    while animate_mouth:
        word = current_word
        for letter in word.upper():
            if letter in letter_to_mouth:
                mouth_image = mouth_images[letter_to_mouth[letter]]

                # Create background image
                background = Image.new("RGB", (320, 240), (5, 254, 255, 255))

                # Position eye image on background
                current_time = time.time()
                eyes_image = closed_eyes_scaled if (current_time - last_blink_time) < 0.5 else open_eyes_scaled
                eyes_x = (320 - eyes_image.width) // 2
                eyes_y = 240 // 10 
                background.paste(eyes_image, (eyes_x, eyes_y), eyes_image)

                # Position mouth image on background
                mouth_x = (320 - mouth_image.width) // 2
                mouth_y = 3 * (240 - mouth_image.height) // 4
                background.paste(mouth_image, (mouth_x, mouth_y), mouth_image)

                # Display image on screen using Matplotlib
                ax.clear()
                ax.imshow(background)
                ax.axis('off')
                plt.pause(0.1)

                # Update blink mechanism
                if current_time - last_blink_time > random.uniform(4, 15):
                    last_blink_time = current_time

        if word == "":
            # Pause when no word to animate
            time.sleep(0.5)

    plt.ioff()  # Turn off interactive mode

def thread_show_mouth_animation():
    thread = threading.Thread(target=show_mouth_animation)
    thread.start()
    return thread

def set_current_word(word):
    global current_word
    current_word = word

def start_speaking(word):
    global animate_mouth
    animate_mouth = True
    set_current_word(word)
    thread = thread_show_mouth_animation()
    return thread

def stop_speaking(thread):
    global animate_mouth, current_word
    animate_mouth = False
    current_word = ""
    thread.join()

# Example of starting and stopping speaking
thread = start_speaking("Hello World")
time.sleep(2)
stop_speaking(thread)
