import cv2
import numpy as np
import time
from uiutils import Button, dog, display
from PIL import Image

button = Button()
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)

color_lower = [np.array([0, 160, 100]), np.array([160, 160, 100])]  
color_upper = [np.array([10, 255, 255]), np.array([179, 255, 255])]
mode = 1

# Skin detection parameters
skin_lower = np.array([0, 133, 77])  
skin_upper = np.array([255, 173, 127])

font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize VideoCapture with color mode
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

def change_color():
    global color_lower, color_upper, mode
    
    color_ranges = [
        ([np.array([0, 160, 100]), np.array([160, 160, 100])], 
         [np.array([10, 255, 255]), np.array([179, 255, 255])]),
        
        ([np.array([40, 60, 75])], [np.array([77, 255, 255])]),
      
        ([np.array([100, 150, 100])], [np.array([120, 255, 255])]),
    
        ([np.array([28, 60, 46])], [np.array([34, 255, 255])])
    ]
    
    mode = (mode % 4) + 1
    color_lower, color_upper = color_ranges[mode - 1]

# FPS counter
t_start = time.time()
fps = 0
color_x = 0
color_y = 0
color_radius = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break
    
    # Ensure we have a 3-channel color image
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    elif frame.shape[2] == 1:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
   
    frame = cv2.flip(frame, 1)
        
    frame_ = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    if mode == 1: 
        mask1 = cv2.inRange(hsv, color_lower[0], color_upper[0])
        mask2 = cv2.inRange(hsv, color_lower[1], color_upper[1])
        mask = cv2.bitwise_or(mask1, mask2)
    else: 
        mask = cv2.inRange(hsv, color_lower[0], color_upper[0])
    
    # Apply skin color filtering
    ycbcr = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    skin_mask = cv2.inRange(ycbcr, skin_lower, skin_upper)
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(skin_mask))
    
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    if len(cnts) > 0:
        cnt = max(cnts, key=cv2.contourArea)
        (color_x, color_y), color_radius = cv2.minEnclosingCircle(cnt)
        if color_radius > 5:
            cv2.circle(frame, (int(color_x), int(color_y)), int(color_radius), (255, 0, 255), 2)
            value_x = color_x - 160
            value_y = color_y - 120
            rider_x = value_x
            value_x = np.clip(value_x, -55, 55)
            value_y = np.clip(value_y, -75, 75)
            
            dog.attitude(['y', 'p'], [value_x / 15, value_y / 15])

    # Display position and FPS
    cv2.putText(frame, "X:%d, Y:%d" % (int(color_x), int(color_y)), (40, 40), font, 0.8, (0, 255, 255), 3)
    
    fps += 1
    mfps = fps / (time.time() - t_start)
    cv2.putText(frame, "FPS " + str(int(mfps)), (40, 80), font, 0.8, (0, 255, 255), 3)

    # Convert and display image
    b, g, r = cv2.split(frame)
    img = cv2.merge((r, g, b))
    colors = [red, green, blue, yellow]
    cv2.rectangle(img, (290, 10), (320, 40), colors[mode - 1], -1)
    
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)  
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if button.press_b():
        break
    if button.press_d():
        change_color()

cap.release()
dog.reset()