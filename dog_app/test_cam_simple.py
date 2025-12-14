import cv2 as cv
import time

def test_camera(index):
    print(f"Testing camera index {index} with V4L2...")
    cap = cv.VideoCapture(index, cv.CAP_V4L2)
    if not cap.isOpened():
        print(f"Failed to open camera index {index}")
        return
    
    print(f"Success! Camera index {index} opened.")
    ret, frame = cap.read()
    if ret:
        print(f"Successfully read a frame of shape {frame.shape}")
    else:
        print("Failed to read frame.")
    cap.release()

if __name__ == "__main__":
    for i in range(2):
        test_camera(i)
    test_camera(-1)
