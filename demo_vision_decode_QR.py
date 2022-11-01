import time
import cv2
import numpy as np
# import zbar
import pyzbar.pyzbar as pyzbar
 
# main函数
if __name__ == '__main__':
    # openCV 字体
    font = cv2.FONT_HERSHEY_SIMPLEX 
    #定义图像源
    cap = cv2.VideoCapture(0)  # 0: use CSI camera,1：use USB camera
    cap.set(3,480) # set Width
    cap.set(4,360) # set Height
    if(not cap.isOpened()):
        print("[camera.py:cam]:can't open this camera")
    
    while(True):
        # 读入图片
        ret, img = cap.read() 
        # 转灰度
        img_ROI_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
 
        # 解码 返回了识别到的多个二维码对象
        barcodes = pyzbar.decode(img_ROI_gray) 
 
        # 对于每个识别到的二维码区域
        for barcode in barcodes:
 
            # 条形码数据为字节对象，所以如果我们想在输出图像上
            # 画出来，就需要先将它转换成字符串
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
            text = "{} ({})".format(barcodeData, barcodeType)
 
            # 打印字符在图片上
            cv2.putText(img, text , (20,100),font,1,(0,255,0),4) 
            # 向终端打印条形码数据和条形码类型
            print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
 
        # 显示
        #cv2.imshow('img_ROI', img_ROI_gray)
        cv2.imshow('image', img)
        if (cv2.waitKey(1)) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows() 