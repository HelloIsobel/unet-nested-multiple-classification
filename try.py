# from PIL import Image
# import numpy as np
#
# path = "data/images/1582701515113.png"
# img = Image.open(path)
# img_nd = np.array(img)  # 将PIL类型转换成numpy类型
# print(len(img_nd.shape))
# print(img.resize)


# a = {"aa": "aa1", "bb": "bb1"}
# print(a["aa"])
# print(a["bb"])

import cv2

path="./data/masks/1582701515096.png"
img=cv2.imread(path)
print(1)