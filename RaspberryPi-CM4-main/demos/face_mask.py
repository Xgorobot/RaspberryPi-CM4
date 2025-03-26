from uiutils import *
import math
import numpy as np


button = Button()
fm = get_dog_type_cache()
print(fm[2])
dog.reset()

pic_path = "./demos/expression/"


import cv2
import mediapipe as mp
font = cv2.FONT_HERSHEY_SIMPLEX
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

def rotation_matrix_to_angles(rotation_matrix):
    """
    Calculate Euler angles from rotation matrix.
    :param rotation_matrix: A 3*3 matrix with the following structure
    [Cosz*Cosy  Cosz*Siny*Sinx - Sinz*Cosx  Cosz*Siny*Cosx + Sinz*Sinx]
    [Sinz*Cosy  Sinz*Siny*Sinx + Sinz*Cosx  Sinz*Siny*Cosx - Cosz*Sinx]
    [  -Siny             CosySinx                   Cosy*Cosx         ]
    :return: Angles in degrees for each axis
    """
    x = math.atan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
    y = math.atan2(-rotation_matrix[2, 0], math.sqrt(rotation_matrix[0, 0] ** 2 +
                                                     rotation_matrix[1, 0] ** 2))
    z = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
    return np.array([x, y, z]) * 180. / math.pi



# For webcam input:
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
cap=cv2.VideoCapture(0)
cap.set(3,320)
cap.set(4,240)
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as face_mesh:
  while cap.isOpened():
    face_coordination_in_real_world = np.array([
        [285, 528, 200],
        [285, 371, 152],
        [197, 574, 128],
        [173, 425, 108],
        [360, 574, 128],
        [391, 425, 108]
    ], dtype=np.float64)

    h=240
    w=320 
    face_coordination_in_image = []
    text=''
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      continue

    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    direction=0
    if results.multi_face_landmarks:
      for face_landmarks in results.multi_face_landmarks:
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_tesselation_style())
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_contours_style())
        mp_drawing.draw_landmarks(
            image=image,
            landmark_list=face_landmarks,
            connections=mp_face_mesh.FACEMESH_IRISES,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_iris_connections_style())
            
        for idx, lm in enumerate(face_landmarks.landmark):
          if idx in [1, 9, 57, 130, 287, 359]:
            x, y = int(lm.x * w), int(lm.y * h)
            face_coordination_in_image.append([x, y])
        face_coordination_in_image = np.array(face_coordination_in_image,dtype=np.float64)
        focal_length = 1 * w
        cam_matrix = np.array([[focal_length, 0, w / 2],
                               [0, focal_length, h / 2],
                               [0, 0, 1]])
        dist_matrix = np.zeros((4, 1), dtype=np.float64)
        success, rotation_vec, transition_vec = cv2.solvePnP(face_coordination_in_real_world, face_coordination_in_image,cam_matrix, dist_matrix)
        rotation_matrix, jacobian = cv2.Rodrigues(rotation_vec)
        result = rotation_matrix_to_angles(rotation_matrix)
        print(result)
        pitch=round(-result[0]/100*20)
        yaw=round(result[1]/80*15)
        roll=round(result[2]/80*15)
        if abs(yaw)<= 4:
            if abs(pitch)<3:
                pitch = round( pitch * 7 )
                print("pitch11",pitch)
                if pitch < -7:
                    print("hello")
                    pitch = -3
                    print("pitch",pitch)
                elif pitch > 7:
                    pitch = 3
                    print("picth",pitch)
            else:
                pitch = pitch
                print("pitch",pitch)
                yaw = 0
                roll = 0
        else:
            pitch = -3
            yaw = yaw 
            if abs(roll) >29:
                roll = round(roll/6)
            else:
                roll = roll
        print("pitch,yaw,roll",pitch,yaw,roll)
        print(fm[2])
        dog.attitude(['p','y','r'],[pitch,yaw,roll])
    else:
      pass
    b,g,r = cv2.split(image)
    image = cv2.merge((r,g,b))
    image = cv2.flip(image, 1)
    try:
      for i, info in enumerate(zip(('Pitch', 'Roll', 'Yaw'), result)):
        k, v = info
        text = f'{k}: {int(v)}'
        cv2.putText(image, text, (20, i*30 + 20),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
    except:
      pass
    imgok = Image.fromarray(image)
    display.ShowImage(imgok)
    if cv2.waitKey(5) & 0xFF == 27:
      break
    if button.press_b():
      break
cap.release()
dog.reset()
