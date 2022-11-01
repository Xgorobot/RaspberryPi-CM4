import numpy as np 
import os
from skimage import feature as ft 
import cv2

img_label = {"Straight": 0, "Turn left": 1, "Turn right": 2, "stop": 3, "background": 4}
def hog_feature(img_array, resize=(64,64)):
    ##提取HOG特征

    img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, resize)
    bins = 9
    cell_size = (8, 8)
    cpb = (2, 2)
    norm = "L2"
    features = ft.hog(img, orientations=bins, pixels_per_cell=cell_size, 
                        cells_per_block=cpb, block_norm=norm, transform_sqrt=True)
    return features

def extra_hog_features_dir(img_dir, write_txt, resize=(64,64)):
    ##提取目录中所有图像HOG特征
   
    img_names = os.listdir(img_dir)
    img_names = [os.path.join(img_dir, img_name) for img_name in img_names]
    if os.path.exists(write_txt):
        os.remove(write_txt)
    
    with open(write_txt, "a") as f:
        index = 0
        for img_name in img_names:
            img_array = cv2.imread(img_name)
            features = hog_feature(img_array, resize)
            label_name = img_name.split("/")[-1].split("_")[0]
            label_num = img_label[label_name]
            row_data = img_name + "\t" + str(label_num) + "\t"
            
            for element in features:
                row_data = row_data + str(round(element,3)) + " "
            row_data = row_data + "\n"
            f.write(row_data)
            
            if index%100 == 0:
                print ("total image number = ", len(img_names), "current image number = ", index)
            index += 1


if __name__ == "__main__":
    img_dir = "/home/xiao5/Desktop/Traffic_sign_recognition/data/HogTrain_affine"
    write_txt = "/home/xiao5/Desktop/Traffic_sign_recognition/data/imgTrain_hog.txt"
    extra_hog_features_dir(img_dir, write_txt, resize=(64,64))
    print ("done")
