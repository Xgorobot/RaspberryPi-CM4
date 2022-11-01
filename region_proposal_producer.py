import os
import numpy as np
import cv2
import xml.etree.ElementTree as ET

cls_names = ["Speed_limit_5","Speed_limit_15","Speed_limit_30",
"Speed_limit_40","Speed_limit_50","Speed_limit_60","Speed_limit_70",
"Speed_limit_80","No straight or right turn","No straight or left turn",
"No straight","No left turn","Do not turn left and right","No right turn",
"No Overhead","No U-turn","No Motor vehicle","No whistle","Unrestricted speed_40","Unrestricted speed_50",
"Straight or turn right","Straight","Turn left","Turn left or turn right","Turn right","Drive on the left side of the road",
"Drive on the right side of the road","Driving around the island",
"Motor vehicle driving","Whistle","Non-motorized","U-turn",
"Left-right detour","traffic light","Drive cautiously","Caution Pedestrians",
"Attention non-motor vehicle","Mind the children",
"Sharp turn to the right","Sharp turn to the left","Downhill steep slope",
"Uphill steep slope","Go slow","Right T-shaped cross","Left T-shaped cross",
"village","Reverse detour","Railway crossing-1","construction","Continuous detour",
"Railway crossing-2","Accident-prone road section","stop",
"No passing","No Parking","No entry","Deceleration and concession","Stop For Check",
]
img_label = {
"000":"Speed_limit_5",
"001":"Speed_limit_15",
"002":"Speed_limit_30",
"003":"Speed_limit_40",
"004":"Speed_limit_50",
"005":"Speed_limit_60",
"006":"Speed_limit_70",
"007":"Speed_limit_80",
"008":"No straight or right turn",
"009":"No straight or left turn",
"010":"No straight",
"011":"No left turn",
"012":"Do not turn left and right",
"013":"No right turn",
"014":"No Overhead",
"015":"No U-turn",
"016":"No Motor vehicle",
"017":"No whistle",
"018":"Unrestricted speed_40",
"019":"Unrestricted speed_50",
"020":"Straight or turn right",
"021":"Straight",
"022":"Turn left",
"023":"Turn left or turn right",
"024":"Turn right",
"025":"Drive on the left side of the road",
"026":"Drive on the right side of the road",
"027":"Driving around the island",
"028":"Motor vehicle driving",
"029":"Whistle",
"030":"Non-motorized",
"031":"U-turn",
"032":"Left-right detour",
"033":"traffic light",
"034":"Drive cautiously",
"035":"Caution Pedestrians",
"036":"Attention non-motor vehicle",
"037":"Mind the children",
"038":"Sharp turn to the right",
"039":"Sharp turn to the left",
"040":"Downhill steep slope",
"041":"Uphill steep slope",
"042":"Go slow",
"044":"Right T-shaped cross",
"043":"Left T-shaped cross",
"045":"village",
"046":"Reverse detour",
"047":"Railway crossing-1",
"048":"construction",
"049":"Continuous detour",
"050":"Railway crossing-2",
"051":"Accident-prone road section",
"052":"stop",
"053":"No passing",
"054":"No Parking",
"055":"No entry",
"056":"Deceleration and concession",
"057":"Stop For Check"
}
target_class=["021","022","024","52"]##所要识别的交通指示牌
classes_name = ["Straight", "Turn left", "Turn right", "stop", "background"]
classes_num = {"Straight": 0, "Turn left": 1, "Turn right": 2, "stop": 3, "background": 4}

SIGN_ROOT = "/home/xiao5/Desktop/Traffic_sign_recognition"
DATA_PATH = os.path.join(SIGN_ROOT, 'data/realTrain/')


def parse_xml(xml_file):
	##返回该图片矩形对焦顶点坐标以及交通标志类型
	tree = ET.parse(xml_file)
	root = tree.getroot()
	image_path = ''
	labels = []

	for item in root:
		if item.tag == 'filename':
			image_path = os.path.join(DATA_PATH, "PNGImages/", item.text)
		elif item.tag == 'object':
			obj_name = item[0].text
			obj_num = classes_num[obj_name]
			xmin = int(item[4][0].text)
			ymin = int(item[4][1].text)
			xmax = int(item[4][2].text)
			ymax = int(item[4][3].text)
			labels.append([xmin, ymin, xmax, ymax, obj_num])
	return image_path,labels

def produce_neg_proposals(img_path, write_dir, min_size, square=False, proposal_num=0):
	##返回其他类型的交通标志裁剪图的数目
	img = cv2.imread(img_path)
	rows = img.shape[0]
	cols = img.shape[1]
	imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	imgBinBlue = cv2.inRange(imgHSV,np.array([110,43,46]), np.array([124,255,255]))
	imgBinRed = cv2.inRange(imgHSV,np.array([165,43,46]), np.array([180,255,255]))
	imgBin = np.maximum(imgBinRed, imgBinBlue)

	contours, _ = cv2.findContours(imgBin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
	for contour in contours:
		x,y,w,h = cv2.boundingRect(contour)
		if w<min_size or h<min_size:
			continue

		if square is True:
			xcenter = int(x+w/2)
			ycenter = int(y+h/2)
			size = max(w,h)
			xmin = int(round(max(xcenter-size/2, 0),0))
			xmax = int(round(min(xcenter+size/2,cols),0))
			ymin = int(round(max(ycenter-size/2, 0),0))
			ymax = int(round(min(ycenter+size/2,rows),0))
			proposal = img[ymin:ymax, xmin:xmax]
			proposal = cv2.resize(proposal, (size,size))

		else:
			proposal = img[y:y+h, x:x+w]
		write_name = "background" + "_" + str(proposal_num) + ".png"
		proposal_num += 1
		cv2.imwrite(os.path.join(write_dir,write_name), proposal)##保存其他类型交通标志裁剪后的图像
	return proposal_num

def produce_pos_proposals(img_path, write_dir, labels, min_size, square=False, proposal_num=0, ):
	##更新目标交通标志裁剪图的数目,返回proposal_num对象
	img = cv2.imread(img_path)
	rows = img.shape[0]
	cols = img.shape[1]
	for label in labels:
		xmin, ymin, xmax, ymax, cls_num = np.int32(label)
		if xmax-xmin<min_size or ymax-ymin<min_size:
			continue
		if square is True:
			xcenter = int((xmin + xmax)/2)
			ycenter = int((ymin + ymax)/2)
			size = max(xmax-xmin, ymax-ymin)
			xmin = int(round(max(xcenter-size/2, 0)))
			xmax = int(round(min(xcenter+size/2,cols)))
			ymin = int(round(max(ycenter-size/2, 0)))
			ymax = int(round(min(ycenter+size/2,rows)))
			proposal = img[ymin:ymax, xmin:xmax]
			proposal = cv2.resize(proposal, (size,size))
		else:
			proposal = img[ymin:ymax, xmin:xmax]
				
		cls_name = classes_name[cls_num]
		proposal_num[cls_name] +=1
		write_name = cls_name + "_" + str(proposal_num[cls_name]) + ".png"
		cv2.imwrite(os.path.join(write_dir,write_name), proposal)
	return proposal_num


def produce_proposals(xml_dir, write_dir, square=False, min_size=30):
                ##返回proposal_num对象
	proposal_num = {}
	for cls_name in classes_name:
		proposal_num[cls_name] = 0
               ##img_names = os.listdir(img_dir)
               ##img_names = [os.path.join(img_dir, img_name) for img_name in img_names]
	index = 0
	for xml_file in os.listdir(xml_dir):
		img_path, labels = parse_xml(os.path.join(xml_dir,xml_file))
		img = cv2.imread(img_path)
		##如果图片中没有出现定义的那几种交通标志就把它当成负样本
		if len(labels) == 0:
			neg_proposal_num = produce_neg_proposals(img_path, write_dir, min_size, square, proposal_num["background"])
			proposal_num["background"] = neg_proposal_num
		else:
			proposal_num = produce_pos_proposals(img_path, write_dir, labels, min_size, square=True, proposal_num=proposal_num)
			
		if index%100 == 0:
			print ("total xml file number = ", len(os.listdir(xml_dir)), "current xml file number = ", index)
			print ("proposal num = ", proposal_num)
		index += 1

	return proposal_num

if __name__ == "__main__":
	xml_dir = "/home/xiao5/Desktop/Traffic_sign_recognition/data/realTrain/Annotations"
	save_dir = "/home/xiao5/Desktop/Traffic_sign_recognition/data/dataTrain"
	proposal_num = produce_proposals(xml_dir, save_dir, square=True)
	print ("proposal num = ", proposal_num)

