import cv2
import time
import tensorflow as tf
import numpy as np
import os,socket,sys,time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from PIL import Image,ImageDraw,ImageFont
from key import Button
import mediapipe as mp
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import math
from xgolib import XGO
dog = XGO("xgolite") 
version=dog.read_firmware()
if version[0]=='M':
    print('XGO-MINI')
    dog = XGO("xgomini")
    dog_type='M'
else:
    print('XGO-LITE')
    dog_type='L'

# def load_X(X_path):
#     file = open(X_path, "r")
#     X_ = np.array([elem for elem in [row.split(",") for row in file]], dtype=np.float32)
#     file.close()
#     return X_


def euclidean_dist(a, b):
    # This function calculates the euclidean distance between 2 point in 2-D coordinates
    # if one of two points is (0,0), dist = 0
    # a, b: input array with dimension: m, 2
    # m: number of samples
    # 2: x and y coordinate
    try:
        if a.shape[1] == 2 and a.shape == b.shape:
            # check if element of a and b is (0,0)
            bol_a = (a[:, 0] != 0).astype(int)
            bol_b = (b[:, 0] != 0).astype(int)
            dist = np.linalg.norm(a - b, axis=1)
            return (dist * bol_a * bol_b).reshape(a.shape[0], 1)
    except:
        print("[Error]: Check dimension of input vector")
        return 0


def norm_X(X):
    num_sample = X.shape[0]
    # Keypoints
    Nose = X[:, 0 * 2 : 0 * 2 + 2]
    Neck = X[:, 1 * 2 : 1 * 2 + 2]
    RShoulder = X[:, 2 * 2 : 2 * 2 + 2]
    RElbow = X[:, 3 * 2 : 3 * 2 + 2]
    RWrist = X[:, 4 * 2 : 4 * 2 + 2]
    LShoulder = X[:, 5 * 2 : 5 * 2 + 2]
    LElbow = X[:, 6 * 2 : 6 * 2 + 2]
    LWrist = X[:, 7 * 2 : 7 * 2 + 2]
    RHip = X[:, 8 * 2 : 8 * 2 + 2]
    RKnee = X[:, 9 * 2 : 9 * 2 + 2]
    RAnkle = X[:, 10 * 2 : 10 * 2 + 2]
    LHip = X[:, 11 * 2 : 11 * 2 + 2]
    LKnee = X[:, 12 * 2 : 12 * 2 + 2]
    LAnkle = X[:, 13 * 2 : 13 * 2 + 2]
    REye = X[:, 14 * 2 : 14 * 2 + 2]
    LEye = X[:, 15 * 2 : 15 * 2 + 2]
    REar = X[:, 16 * 2 : 16 * 2 + 2]
    LEar = X[:, 17 * 2 : 17 * 2 + 2]

    # Length of head
    length_Neck_LEar = euclidean_dist(Neck, LEar)
    length_Neck_REar = euclidean_dist(Neck, REar)
    length_Neck_LEye = euclidean_dist(Neck, LEye)
    length_Neck_REye = euclidean_dist(Neck, REye)
    length_Nose_LEar = euclidean_dist(Nose, LEar)
    length_Nose_REar = euclidean_dist(Nose, REar)
    length_Nose_LEye = euclidean_dist(Nose, LEye)
    length_Nose_REye = euclidean_dist(Nose, REye)
    length_head = np.maximum.reduce(
        [
            length_Neck_LEar,
            length_Neck_REar,
            length_Neck_LEye,
            length_Neck_REye,
            length_Nose_LEar,
            length_Nose_REar,
            length_Nose_LEye,
            length_Nose_REye,
        ]
    )
    # length_head      = np.sqrt(np.square((LEye[:,0:1]+REye[:,0:1])/2 - Neck[:,0:1]) + np.square((LEye[:,1:2]+REye[:,1:2])/2 - Neck[:,1:2]))

    # Length of torso
    length_Neck_LHip = euclidean_dist(Neck, LHip)
    length_Neck_RHip = euclidean_dist(Neck, RHip)
    length_torso = np.maximum(length_Neck_LHip, length_Neck_RHip)
    # length_torso     = np.sqrt(np.square(Neck[:,0:1]-(LHip[:,0:1]+RHip[:,0:1])/2) + np.square(Neck[:,1:2]-(LHip[:,1:2]+RHip[:,1:2])/2))

    # Length of right leg
    length_leg_right = euclidean_dist(RHip, RKnee) + euclidean_dist(RKnee, RAnkle)
    # length_leg_right = np.sqrt(np.square(RHip[:,0:1]-RKnee[:,0:1]) + np.square(RHip[:,1:2]-RKnee[:,1:2])) \
    # + np.sqrt(np.square(RKnee[:,0:1]-RAnkle[:,0:1]) + np.square(RKnee[:,1:2]-RAnkle[:,1:2]))

    # Length of left leg
    length_leg_left = euclidean_dist(LHip, LKnee) + euclidean_dist(LKnee, LAnkle)
    # length_leg_left = np.sqrt(np.square(LHip[:,0:1]-LKnee[:,0:1]) + np.square(LHip[:,1:2]-LKnee[:,1:2])) \
    # + np.sqrt(np.square(LKnee[:,0:1]-LAnkle[:,0:1]) + np.square(LKnee[:,1:2]-LAnkle[:,1:2]))

    # Length of leg
    length_leg = np.maximum(length_leg_right, length_leg_left)

    # Length of body
    length_body = length_head + length_torso + length_leg

    # Check all samples have length_body of 0
    length_chk = (length_body > 0).astype(int)

    # Check keypoints at origin
    keypoints_chk = (X > 0).astype(int)

    chk = length_chk * keypoints_chk

    # Set all length_body of 0 to 1 (to avoid division by 0)
    length_body[length_body == 0] = 1

    # The center of gravity
    # number of point OpenPose locates:
    num_pts = (X[:, 0::2] > 0).sum(1).reshape(num_sample, 1)
    centr_x = X[:, 0::2].sum(1).reshape(num_sample, 1) / num_pts
    centr_y = X[:, 1::2].sum(1).reshape(num_sample, 1) / num_pts

    # The  coordinates  are  normalized relative to the length of the body and the center of gravity
    X_norm_x = (X[:, 0::2] - centr_x) / length_body
    X_norm_y = (X[:, 1::2] - centr_y) / length_body

    # Stack 1st element x and y together
    X_norm = np.column_stack((X_norm_x[:, :1], X_norm_y[:, :1]))

    for i in range(1, X.shape[1] // 2):
        X_norm = np.column_stack(
            (X_norm, X_norm_x[:, i : i + 1], X_norm_y[:, i : i + 1])
        )

    # Set all samples have length_body of 0 to origin (0, 0)
    X_norm = X_norm * chk

    return X_norm


# encodings for labels in dataset
LABELS = [
    "squats",
    "lunges",
    "bicep_curls",
    "situps",
    "pushups",
    "tricep_extensions",
    "dumbbell_rows",
    "jumping_jacks",
    "dumbbell_shoulder_press",
    "lateral_shoulder_raises",
]
action_dict = {
    "squats" : 6,
    "lunges" : 1,
    "bicep_curls" :19,
    "situps" : -1,
    "pushups" : 21,
    "tricep_extensions" :19,
    "dumbbell_rows" :-1,
    "jumping_jacks" :-1,
    "dumbbell_shoulder_press" :12,
    "lateral_shoulder_raises" :13,
}

class_d = {}
for i, ex in enumerate(LABELS):
    class_d[ex] = i


class DeepFitClassifier:
    def __init__(self, model_path):
        """
        Load the TFLite model and allocate tensors \n
        Get input and output tensors.
        """
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def predict(self, X) -> str:
        """
        X -> (1, 36) shaped numpy array
        First 18 are the x coordinates of the 18 keypoints \n
        next 18 are the y coordinates of the 18 keypoints \n
        Returns: \n
        Winning Label
        """
        # Setup input
        X_sample = np.array(X).reshape(1, -1)
        X_sample_norm = norm_X(X_sample)
        input_data = np.array(X_sample_norm[0], np.float32).reshape(1, 36)
        # Invoke the model on the input data
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        # Get the result
        output_data = self.interpreter.get_tensor(self.output_details[0]["index"])

        np_output_data = np.array(output_data)
        champ_idx = np.argmax(np_output_data)
        prob =  np_output_data[0][champ_idx]
        self.results = dict(zip(LABELS, output_data[0]))

        return LABELS[champ_idx], prob

    def get_results(self) -> dict:
        """
        Get a dictionary containing the probability of each label for the last predicted input
        """
        return self.results
        # return 0
        
lm_dict = {
  0:0 , 1:10, 2:12, 3:14, 4:16, 5:11, 6:13, 7:15, 8:24, 9:26, 10:28, 11:23, 12:25, 13:27, 14:5, 15:2, 16:8, 17:7,
}



def set_pose_parameters():
    mode = False 
    complexity = 1
    smooth_landmarks = True
    enable_segmentation = False
    smooth_segmentation = True
    detectionCon = 0.5
    trackCon = 0.5
    mpPose = mp.solutions.pose
    return mode,complexity,smooth_landmarks,enable_segmentation,smooth_segmentation,detectionCon,trackCon,mpPose


def get_pose (img, results, draw=True):        
        if results.pose_landmarks:
            if draw:
                mpDraw = mp.solutions.drawing_utils
                mpDraw.draw_landmarks(img,results.pose_landmarks,
                                           mpPose.POSE_CONNECTIONS) 
        return img

def get_position(img, results, height, width, draw=True ):
        landmark_list = []
        if results.pose_landmarks:
            for id, landmark in enumerate(results.pose_landmarks.landmark):
                #finding height, width of the image printed
                height, width, c = img.shape
                #Determining the pixels of the landmarks
                landmark_pixel_x, landmark_pixel_y = int(landmark.x * width), int(landmark.y * height)
                landmark_list.append([id, landmark_pixel_x, landmark_pixel_y])
                if draw:
                    cv2.circle(img, (landmark_pixel_x, landmark_pixel_y), 5, (255,0,0), cv2.FILLED)
        return landmark_list    


def get_angle(img, landmark_list, point1, point2, point3, draw=True):   
        #Retrieve landmark coordinates from point identifiers
        x1, y1 = landmark_list[point1][1:]
        x2, y2 = landmark_list[point2][1:]
        x3, y3 = landmark_list[point3][1:]
            
        angle = math.degrees(math.atan2(y3-y2, x3-x2) - 
                             math.atan2(y1-y2, x1-x2))
        
        #Handling angle edge cases: Obtuse and negative angles
        if angle < 0:
            angle += 360
            if angle > 180:
                angle = 360 - angle
        elif angle > 180:
            angle = 360 - angle
            
        if draw:
            #Drawing lines between the three points
            cv2.line(img, (x1, y1), (x2, y2), (255,255,255), 3)
            cv2.line(img, (x3, y3), (x2, y2), (255,255,255), 3)

            #Drawing circles at intersection points of lines
            cv2.circle(img, (x1, y1), 5, (75,0,130), cv2.FILLED)
            cv2.circle(img, (x1, y1), 15, (75,0,130), 2)
            cv2.circle(img, (x2, y2), 5, (75,0,130), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (75,0,130), 2)
            cv2.circle(img, (x3, y3), 5, (75,0,130), cv2.FILLED)
            cv2.circle(img, (x3, y3), 15, (75,0,130), 2)
            
            #Show angles between lines
            cv2.putText(img, str(int(angle)), (x2-50, y2+50), 
                        cv2.FONT_HERSHEY_PLAIN, 1.0, (0,0,255), 2)
        return angle

    
    
def convert_mediapipe_keypoints_for_model(lm_dict, landmark_list):
    inp_pushup = []
    for index in range(0, 36):
        if index < 18:
            inp_pushup.append(round(landmark_list[lm_dict[index]][1],3))
        else:
            inp_pushup.append(round(landmark_list[lm_dict[index-18]][2],3))
    return inp_pushup



# Setting variables for video feed
def set_video_feed_variables():
    cap = cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)
    count = 0
    direction = 0
    form = 0
    feedback = "Bad Form."
    frame_queue = deque(maxlen=250)
    clf = DeepFitClassifier('/home/pi/RaspberryPi-CM4-main/demos/deepfit_classifier_v3.tflite')
    return cap,count,direction,form,feedback,frame_queue,clf


def set_percentage_bar_and_text(elbow_angle, knee_angle, workout_name_after_smoothening):
    if workout_name_after_smoothening == "pushups":    
        pushup_success_percentage = np.interp(elbow_angle, (90, 160), (0, 100))
        pushup_progress_bar = np.interp(elbow_angle, (90, 160), (380, 30))
        return pushup_success_percentage,pushup_progress_bar
    # Else only handles squats right now
    else:
        pushup_success_percentage = np.interp(knee_angle, (90, 160), (0, 100))
        pushup_progress_bar = np.interp(knee_angle, (90, 160), (380, 30))
        return pushup_success_percentage,pushup_progress_bar

def set_body_angles_from_keypoints(get_angle, img, landmark_list):
    elbow_angle = get_angle(img, landmark_list, 11, 13, 15)
    shoulder_angle = get_angle(img, landmark_list, 13, 11, 23)
    hip_angle = get_angle(img, landmark_list, 11, 23,25)
    elbow_angle_right = get_angle(img, landmark_list, 12, 14, 16)
    shoulder_angle_right = get_angle(img, landmark_list, 14, 12, 24)
    hip_angle_right = get_angle(img, landmark_list, 12, 24,26)
    knee_angle = get_angle(img, landmark_list, 24,26, 28)
    return elbow_angle,shoulder_angle,hip_angle,elbow_angle_right,shoulder_angle_right,hip_angle_right,knee_angle

def set_smoothened_workout_name(lm_dict, convert_mediapipe_keypoints_for_model, frame_queue, clf, landmark_list):
    inp_pushup = convert_mediapipe_keypoints_for_model(lm_dict, landmark_list)
    workout_name, prob = clf.predict(inp_pushup)
    frame_queue.append(workout_name)
    workout_name_after_smoothening = max(set(frame_queue), key=frame_queue.count)
    return "Workout Name: " + workout_name_after_smoothening, prob

def run_full_workout_motion(count, direction, form, elbow_angle, shoulder_angle, hip_angle, elbow_angle_right, shoulder_angle_right, hip_angle_right, knee_angle, pushup_success_percentage, feedback, workout_name_after_smoothening):
    if workout_name_after_smoothening.strip() == "pushups":
        if form == 1:
            if pushup_success_percentage == 0:
                if elbow_angle <= 90 and hip_angle > 160 and elbow_angle_right <= 90 and hip_angle_right > 160:
                    feedback = "Feedback: Go Up"
                    if direction == 0:
                        count += 0.5
                        direction = 1
                else:
                    feedback = "Feedback: Bad Form."
                        
            if pushup_success_percentage == 100:
                if elbow_angle > 160 and shoulder_angle > 40 and hip_angle > 160 and elbow_angle_right > 160 and shoulder_angle_right > 40 and hip_angle_right > 160:
                    feedback = "Feedback: Go Down"
                    if direction == 1:
                        count += 0.5
                        direction = 0
                else:
                    feedback = "Feedback: Bad Form."
        return [feedback, count]
    # For now, else condition handles just squats
    elif workout_name_after_smoothening.strip() == "squats":
        if form == 1:
            if pushup_success_percentage == 0:
                if knee_angle < 90:
                    feedback = "Go Up"
                    if direction == 0:
                        count += 0.5
                        direction = 1
                else:
                    feedback = "Feedback: Bad Form."                    
            if pushup_success_percentage == 100:
                if knee_angle > 169:
                    feedback = "Feedback: Go Down"
                    if direction == 1:
                        count += 0.5
                        direction = 0
                else:
                    feedback = "Feedback: Bad Form."
            return [feedback, count]
    else:
        return ["Feedback:",0]

def draw_percentage_progress_bar(form, img, pushup_success_percentage, pushup_progress_bar):
    xd, yd, wd, hd = 10, 175, 50, 200
    if form == 1:
        cv2.rectangle(img, (xd,30), (xd+wd, yd+hd), (0, 255, 0), 3)
        cv2.rectangle(img, (xd, int(pushup_progress_bar)), (xd+wd, yd+hd), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(pushup_success_percentage)}%', (xd, yd+hd+50), cv2.FONT_HERSHEY_PLAIN, 2,
                        (255, 0, 0), 2)

def display_rep_count(count, img):
    xc, yc = 20, 60
    cv2.putText(img, "Reps: " + str(int(count)), (xc, yc), cv2.FONT_HERSHEY_PLAIN, 1.0,
                    (255, 0, 0), 2)

def show_workout_feedback(feedback, img):    
    xf, yf = 20, 40
    cv2.putText(img, feedback, (xf, yf), cv2.FONT_HERSHEY_PLAIN, 1.0,
                    (0,0,0), 2)

def show_workout_name_from_model(img, workout_name_after_smoothening):
    xw, yw = 20, 20
    cv2.putText(img, workout_name_after_smoothening, (xw,yw), cv2.FONT_HERSHEY_PLAIN, 1.0,
                    (0,0,0), 2)

def check_form(elbow_angle, shoulder_angle, hip_angle, elbow_angle_right, shoulder_angle_right, hip_angle_right, knee_angle, form, workout_name_after_smoothening):
    if workout_name_after_smoothening == "pushups":
        if elbow_angle > 160 and shoulder_angle > 40 and hip_angle > 160 and elbow_angle_right > 160 and shoulder_angle_right > 40 and hip_angle_right > 160:
            form = 1
    # For now, else impleements squats condition        
    else:
        if knee_angle > 160:
            form = 1
    return form

def display_workout_stats(count, form, feedback, draw_percentage_progress_bar, display_rep_count, show_workout_feedback, show_workout_name_from_model, img, pushup_success_percentage, pushup_progress_bar, workout_name_after_smoothening):
    #Draw the pushup progress bar
    # draw_percentage_progress_bar(form, img, pushup_success_percentage, pushup_progress_bar)

    #Show the rep count
    display_rep_count(count, img)
        
    #Show the pushup feedback 
    show_workout_feedback(feedback, img)
        
    #Show workout name
    show_workout_name_from_model(img, workout_name_after_smoothening)




display = LCD_2inch.LCD_2inch()
display.clear()
splash = Image.new("RGB", (display.height, display.width ),"black")
display.ShowImage(splash)
button=Button()

# cap=cv2.VideoCapture(0)
# cap.set(3,320)
# cap.set(4,240)
# input_width, input_height = 352, 352

mode, complexity, smooth_landmarks, enable_segmentation, smooth_segmentation, detectionCon, trackCon, mpPose = set_pose_parameters()
pose = mpPose.Pose(mode, complexity, smooth_landmarks,
                            enable_segmentation, smooth_segmentation,
                            detectionCon, trackCon)


# Setting video feed variables
cap, count, direction, form, feedback, frame_queue, clf = set_video_feed_variables()



#Start video feed and run workout
width  = cap.get(3)  
height = cap.get(4)  
workout_pre = ""
workout_pre_detection_times = 0
while cap.isOpened():
    #Getting image from camera
    start = time.perf_counter()
    ret, img = cap.read() 
    img = cv2.flip(img,1)
    #Getting video dimensions
    
    #Convert from BGR (used by cv2) to RGB (used by Mediapipe)
    start_1 = time.perf_counter()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(img) # 155ms
    end_1 = time.perf_counter()
    times = (end_1 - start_1) * 1000.    #80ms
    print("process :%fms"%times)
    
    #Get pose and draw landmarks
    
    img = get_pose(img, results, False)
    
    # Get landmark list from mediapipe
    landmark_list = get_position(img, results, height, width, False)
    
   
    
    #If landmarks exist, get the relevant workout body angles and run workout. The points used are identifiers for specific joints
    if len(landmark_list) != 0:
        elbow_angle, shoulder_angle, hip_angle, elbow_angle_right, shoulder_angle_right, hip_angle_right, knee_angle = set_body_angles_from_keypoints(get_angle, img, landmark_list)
        
        workout_name_after_smoothening, prob = set_smoothened_workout_name(lm_dict, convert_mediapipe_keypoints_for_model, frame_queue, clf, landmark_list)    

        workout_name_after_smoothening = workout_name_after_smoothening.replace("Workout Name:", "").strip()
        pushup_success_percentage, pushup_progress_bar = set_percentage_bar_and_text(elbow_angle, knee_angle, workout_name_after_smoothening)
    
                
        #Is the form correct at the start?
        form = check_form(elbow_angle, shoulder_angle, hip_angle, elbow_angle_right, shoulder_angle_right, hip_angle_right, knee_angle, form, workout_name_after_smoothening)
    
        #Full workout motion
        if workout_name_after_smoothening.strip() == "pushups":
            if form == 1:
                if pushup_success_percentage == 0:
                    if elbow_angle <= 90 and hip_angle > 160 and elbow_angle_right <= 90 and hip_angle_right > 160:
                        feedback = "Feedback: Go Up"
                        if direction == 0:
                            count += 0.5
                            direction = 1
                    else:
                        feedback = "Feedback: Bad Form."
                            
                if pushup_success_percentage == 100:
                    if elbow_angle > 160 and shoulder_angle > 40 and hip_angle > 160 and elbow_angle_right > 160 and shoulder_angle_right > 40 and hip_angle_right > 160:
                        feedback = "Feedback: Go Down"
                        if direction == 1:
                            count += 0.5
                            direction = 0
                    else:
                        feedback = "Feedback: Bad Form."
        # For now, else condition handles just squats
        elif workout_name_after_smoothening.strip() == "squats":
            if form == 1:
                if pushup_success_percentage == 0:
                    if knee_angle < 90:
                        feedback = "Go Up"
                        if direction == 0:
                            count += 0.5
                            direction = 1
                    else:
                        feedback = "Feedback: Bad Form."                    
                if pushup_success_percentage == 100:
                    if knee_angle > 169:
                        feedback = "Feedback: Go Down"
                        if direction == 1:
                            count += 0.5
                            direction = 0
                    else:
                        feedback = "Feedback: Bad Form."
        
        
        
 
        
        #Display workout stats   
        display_workout_stats(count, form, feedback, draw_percentage_progress_bar, display_rep_count, show_workout_feedback, show_workout_name_from_model, img, pushup_success_percentage, pushup_progress_bar, workout_name_after_smoothening)
        
        ## xgo play workout
        if workout_name_after_smoothening.strip() != workout_pre:
            workout_pre_detection_times = 0
            if prob >= 0.8:
                workout_pre = workout_name_after_smoothening.strip()
            else:
                workout_pre = ""
                
        else:
            if prob >= 0.6:
                workout_pre_detection_times += 1
                if workout_pre_detection_times > 4 :
                    action_id = action_dict[workout_pre]
                    if action_id > 0:
                        dog.action(action_id)
                        time.sleep(6)
                    workout_pre_detection_times = 0
                    workout_pre = ""
    else:
        workout_pre_detection_times = 0
        workout_pre = ""
            
        

        
    # Transparent Overlay
    overlay = img.copy()
    x, y, w, h = 15, 10, 200, 50
    cv2.rectangle(img, (x, y), (x+w, y+h), (255,255,255), -1)      
    alpha = 0.8  # Transparency factor.
    # Following line overlays transparent rectangle over the image
    image_new = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)          
        

    imgok = Image.fromarray(image_new)    
    display.ShowImage(imgok)    # 46ms
    if cv2.waitKey(5) & 0xFF == 27:
      break
    if button.press_b():
      break
    end = time.perf_counter()
    times = (end - start) * 1000.    #80ms
    print("forward time:%fms"%times)
        
cap.release()



        

          
