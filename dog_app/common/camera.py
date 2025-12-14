import cv2 as cv
import time

class DogCamera: # Renamed class for consistency
    def __init__(self, video_id=0, width=640, height=480, debug=False):
        self.__debug = debug
        self.__video_id = video_id
        self.__state = False # True if camera is successfully opened
        self.__width = width
        self.__height = height

        print(f"DogCamera: Initializing camera with video_id={video_id}...")
        self.__video = cv.VideoCapture(self.__video_id)
        # Match ball.py settings
        self.__video.set(cv.CAP_PROP_FRAME_WIDTH, 320)
        self.__video.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
        self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        # Try alternative camera ID if the first one fails
        if not self.__video.isOpened():
            print(f"DogCamera: Failed to open video_id {self.__video_id}. Trying alternative.")
            self.__video_id = (self.__video_id + 1) % 2 
            self.__video.release() 
            self.__video = cv.VideoCapture(self.__video_id)
            self.__video.set(cv.CAP_PROP_FRAME_WIDTH, 320)
            self.__video.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
            self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if self.__video.isOpened():
            self.__state = True
            self.__config_camera()
            if self.__debug:
                print(f"DogCamera: Video{self.__video_id} initialized successfully ({self.__width}x{self.__height}).")
        else:
            self.__state = False
            print(f"DogCamera: Error! Failed to initialize any camera.")
            # self.__video will be None or an unopened VideoCapture object.

    def __del__(self):
        if self.__debug:
            print("DogCamera: Releasing camera resources.")
        if hasattr(self,'__video') and self.__video: # Ensure __video exists
             self.__video.release()
        self.__state = False
        
    def stop(self):
        """Stops the camera to save power (Eco Mode)."""
        if self.__state and self.__video.isOpened():
             print("DogCamera: Stopping camera for Eco Mode.")
             self.__video.release()
        self.__state = False

    def start(self):
        """Restarts the camera (Exit Eco Mode)."""
        if self.__state: return # Already running
        
        print(f"DogCamera: Restarting camera video_id={self.__video_id}...")
        self.__video = cv.VideoCapture(self.__video_id)
        self.__video.set(cv.CAP_PROP_FRAME_WIDTH, 320)
        self.__video.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
        self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        if self.__video.isOpened():
            self.__state = True
            self.__config_camera()
            print("DogCamera: Restart successful.")
            return True
        else:
            print("DogCamera: Restart failed.")
            return False

    def __config_camera(self):
        if not self.__state or not self.__video.isOpened():
            return

        # Attempt to set camera properties
        # OpenCV version check for FOURCC
        cv_edition = cv.__version__
        if cv_edition.startswith('3'): # e.g., 3.4.x
            self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG')) # Try MJPG for broader compatibility
        else: # OpenCV 4.x and later
            self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc('M', 'J', 'P', 'G'))

        self.__video.set(cv.CAP_PROP_FRAME_WIDTH, self.__width)
        self.__video.set(cv.CAP_PROP_FRAME_HEIGHT, self.__height)

        # Verify settings if debugging
        if self.__debug:
            actual_width = self.__video.get(cv.CAP_PROP_FRAME_WIDTH)
            actual_height = self.__video.get(cv.CAP_PROP_FRAME_HEIGHT)
            print(f"DogCamera: Requested {self.__width}x{self.__height}, Actual {actual_width}x{actual_height}")


    def is_opened(self): # Renamed from isOpened to follow Python conventions
        return self.__state and self.__video and self.__video.isOpened()

    def close(self): # Added an explicit close method
        self.__del__()

    def reconnect(self):
        if self.__debug:
            print("DogCamera: Attempting to reconnect...")
        self.close() # Release existing resources

        # Re-initialize
        self.__video = cv.VideoCapture(self.__video_id)
        if not self.__video.isOpened():
            self.__video_id = (self.__video_id + 1) % 2
            self.__video.release()
            self.__video = cv.VideoCapture(self.__video_id)

        if self.__video.isOpened():
            self.__state = True
            self.__config_camera()
            if self.__debug:
                print(f"DogCamera: Video{self.__video_id} reconnected successfully.")
            return True
        else:
            self.__state = False
            if self.__debug:
                print(f"DogCamera: Failed to reconnect camera.")
            return False

    def get_frame(self):
        """Reads a frame from the camera."""
        if not self.is_opened():
            if self.__debug:
                # print("DogCamera: get_frame called but camera not open.")
                pass # Avoid spamming logs if called in a loop
            return False, None

        success, image = self.__video.read()
        if not success:
            if self.__debug:
                print("DogCamera: Failed to read frame from camera.")
            self.__state = False # Mark as not usable if read fails
        return success, image

    def get_frame_jpeg(self, text="", color=(0, 255, 0)): # Renamed from get_frame_jpg
        """Reads a frame, optionally adds text, and returns JPEG encoded bytes."""
        success, image = self.get_frame()
        if not success:
            return False, None # Return None instead of bytes({1}) for clarity

        if text != "": # text was a string in original, ensure it is
            cv.putText(image, str(text), (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) # Slightly larger text

        ret, jpeg_bytes = cv.imencode('.jpg', image, [int(cv.IMWRITE_JPEG_QUALITY), 50])
        if not ret:
            if self.__debug:
                print("DogCamera: Failed to encode frame to JPEG.")
            return False, None
        return True, jpeg_bytes.tobytes()


if __name__ == '__main__':
    print("DogCamera Test Script")
    camera = DogCamera(debug=True)

    if not camera.is_opened():
        print("Camera could not be opened. Exiting test.")
    else:
        print("Camera opened. Press 'q' to quit.")
        fps_counter = 0
        t_start = time.time()

        while True:
            success, frame = camera.get_frame()
            if not success:
                print("Failed to get frame, attempting reconnect...")
                if not camera.reconnect():
                    print("Reconnect failed. Exiting.")
                    break
                continue

            fps_counter += 1
            if time.time() - t_start >= 1.0:
                fps = fps_counter / (time.time() - t_start)
                print(f"FPS: {fps:.2f}")
                fps_counter = 0
                t_start = time.time()

            # Add FPS to frame for display
            # cv.putText(frame, f"FPS: {fps:.2f}" if 'fps' in locals() else "FPS: calculating...",
            #            (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv.imshow('DogCamera Test', frame)

            key = cv.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        camera.close()
        cv.destroyAllWindows()
        print("DogCamera test finished.")
