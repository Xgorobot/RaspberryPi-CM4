from uiutils import Button, display
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar

# Initialize button and camera
button = Button()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

def cv2AddChineseText(img, text, position, textColor=(200, 0, 200), textSize=10, max_width=300):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype("/home/jinliang/model/msyh.ttc", textSize, encoding="utf-8")
    
    lines = []
    current_line = ""
    for char in text:
        # Display line breaks
        test_line = current_line + char
        test_width = draw.textlength(test_line, font=fontStyle)
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    
    x, y = position
    line_height = textSize + 5  
    for line in lines:
        draw.text((x, y), line, textColor, font=fontStyle)
        y += line_height
    
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

while True:
    # Capture and process image
    ret, img = cap.read()
    if not ret:
        break
    
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect barcodes
    barcodes = pyzbar.decode(img_gray) 
    for barcode in barcodes:
        try:
            barcodeData = barcode.data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                barcodeData = barcode.data.decode("gbk")  
            except:
                barcodeData = barcode.data.decode("utf-8", errors="replace")  
        
        barcodeType = barcode.type
        text = "{}".format(barcodeData)
        img = cv2AddChineseText(img, text, (10, 30), (0, 255, 0), 30)
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    
    display.ShowImage(img_pil)
    
    if cv2.waitKey(1) == ord('q'):
        break
    if button.press_b():
        break

cap.release()