import mediapipe as mp
import cv2
 
#（1）创建检测手部关键点的方法
mpHands = mp.solutions.hands  #接收方法
hands = mpHands.Hands(static_image_mode=False, #静态追踪，低于0.5置信度会再一次跟踪
                      max_num_hands=1, # 最多有2只手
                      min_detection_confidence=0.6, # 最小检测置信度
                      min_tracking_confidence=0.5)  # 最小跟踪置信度 
 
# 创建检测手部关键点和关键点之间连线的方法
mpDraw = mp.solutions.drawing_utils
 
# 存放坐标信息
lmList = []
 
#（2）对传入的每一帧图像处理
def handDetector(img):
    length=0
    # 把图像传入检测模型，提取信息
    results = hands.process(img)
    
    # 检查每帧图像是否有多只手，一一提取它们
    if results.multi_hand_landmarks: #如果没有手就是None
        for handlms in results.multi_hand_landmarks:
            
            # 绘制关键点及连线，mpHands.HAND_CONNECTIONS绘制手部关键点之间的连线
            #mpDraw.draw_landmarks(img, handlms, mpHands.HAND_CONNECTIONS) 
 
            # 获取每个关键点的索引和坐标
            for index, lm in enumerate(handlms.landmark):
                
                # 将xy的比例坐标转换成像素坐标
                h, w, c = img.shape # 分别存放图像长\宽\通道数
                
                # 中心坐标(小数)，必须转换成整数(像素坐标)
                cx ,cy =  int(lm.x * w), int(lm.y * h) #比例坐标x乘以宽度得像素坐标
                
                #（3）分别处理拇指"4"和食指"8"的像素坐标
                if index == 4:
                    x1, y1 = cx, cy    
                if index == 8:
                    
                    x2, y2 = cx, cy
                    # 打印坐标信息
                    #print("4", x1, y1, ", 8", x2, y2)
                    
                    # 保存坐标点
                    lmList.append([[x1,y1],[x2,y2]])
                    
                    # 在食指和拇指关键点上画圈，img画板，坐标(cx,cy)，半径5，红色填充
                    cv2.circle(img, (x1,y1), 5, (255,0,0), cv2.FILLED)
                    cv2.circle(img, (x2,y2), 5, (255,0,0), cv2.FILLED)
                
                    # 在拇指和食指中间画一条线段，img画板，起点和终点坐标，颜色，线条宽度
                    cv2.line(img, (x1,y1), (x2,y2), (255,0,255), 3)
                    
                    # 拇指和食指的中点，像素坐标是整数要用//
                    cx, cy = (x1+x2)//2, (y1+y2)//2
                    
                    # 在中点画一个圈
                    cv2.circle(img, (cx,cy), 6, (255,0,0), cv2.FILLED)
                    
                    length=(x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)**0.5
                  
    # 返回处理后的图像，及关键点坐标
    return img, lmList,length