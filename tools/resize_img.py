"""
！！本地运行！！

将第一层文件【cvat_data_final】下所有子文件夹新增
【images_resize】和【masks_resize】两个文件夹，大小均改为(1280, 1024)

cvat_data_final：
    |--yongkang01
        |--images
        |--masks
        |--masks_color
        -----------------新增：
        |--images_resize (1280, 1024)
        |--masks_resize (1280, 1024)
    |--yongkang02
        |--images
        |--masks
        |--masks_color
        -----------------新增：
        |--images_resize (1280, 1024)
        |--masks_resize (1280, 1024)
"""

import cv2
import os

check_dir = lambda d: None if os.path.exists(d) else os.makedirs(d)
path = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\cvat_data_final"

for dirname in os.listdir(path):
    resize_dir=os.path.join(path, os.path.join(dirname, "images_resize"))
    check_dir(resize_dir)
    resize_dir=os.path.join(path, os.path.join(dirname, "masks_resize"))
    check_dir(resize_dir)


for root, dirs, files in os.walk(path):
    for file in files:
        type = file.split('.')[1]
        if type != 'xml':
            imgpath = os.path.join(root, file)
            if "images" in imgpath:
                outpath = imgpath.replace("images", "images_resize")
            if "\masks" in imgpath:
                outpath = imgpath.replace("masks", "masks_resize")
            img = cv2.imread(imgpath)
            img_resize = cv2.resize(img, dsize=(1280, 1024), interpolation=cv2.INTER_LINEAR)
            cv2.imwrite(outpath, img_resize)
