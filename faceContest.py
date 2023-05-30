from XgoContest import *
import os, socket, sys, time
import spidev as SPI
import LCD_2inch
from key import Button
import mediapipe as mp
from numpy import linalg
import cv2
from PIL import Image, ImageDraw, ImageFont

# ---------------------INIT------------------------ #
display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width), "black")
display.ShowImage(splash)
button = Button()
font = cv2.FONT_HERSHEY_SIMPLEX
cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)
if not cap.isOpened():
    print("[camera.py:cam]:can't open this camera")
dog = XgoExtend(port='/dev/ttyAMA0', screen=display, button=button, cap=cap, version="xgomini")
# ---------------------MAIN------------------------ #

dog.calibration_contest()
