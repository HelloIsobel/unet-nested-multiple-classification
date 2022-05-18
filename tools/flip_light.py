# import os
# import cv2
#
# path=r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\zengqiang_src_masks"
# flippath=r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\zengqiang_result_masks"
#
# for img in os.listdir(path):
#     imgpath=os.path.join(path, img)
#     imgname=img.split('.')[0]
#     image = cv2.imread(imgpath)
#
#     # Flipped Horizontally 水平翻转
#     h_flip = cv2.flip(image, 1)
#
#     outpath=os.path.join(flippath, imgname+"_flip.png")
#     cv2.imwrite(outpath, h_flip)

# import cv2
# import numpy as np
# import os
#
# path = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\zengqiang_src_masks"
# flippath = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\masks_v30"
#
# for img in os.listdir(path):
#     imgpath = os.path.join(path, img)
#     imgname = img.split('.')[0]
#     img = cv2.imread(imgpath)
#     # img = cv2.flip(img, 1)
#     #
#     # img_t = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#     # h, s, v = cv2.split(img_t)
#     #
#     # # 增加图像亮度
#     # v1 = np.clip(cv2.add(1 * v, -30), 0, 255)
#     # img1 = np.uint8(cv2.merge((h, s, v1)))
#     # img1 = cv2.cvtColor(img1, cv2.COLOR_HSV2BGR)
#     outpath = os.path.join(flippath, imgname + "_v30.png")
#     cv2.imwrite(outpath, img)
