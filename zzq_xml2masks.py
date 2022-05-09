# 参考网址
# https://towardsdatascience.com/extract-annotations-from-cvat-xml-file-into-mask-files-in-python-bb69749c4dc9
# https://blog.csdn.net/weixin_26713521/article/details/108224875
# 标注网址
# http://101.37.163.116:6701
# name：SiaIsobel  password:email

import os
import cv2
import argparse
import shutil
import numpy as np
from lxml import etree
from tqdm import tqdm


def dir_create(path):
    if (os.path.exists(path)) and (os.listdir(path) != []):
        shutil.rmtree(path)
        os.makedirs(path)
    if not os.path.exists(path):
        os.makedirs(path)


def mask_color(shape, scale_factor, mask, color_):
    points = [tuple(map(float, p.split(',')))
              for p in shape['points'].split(';')]
    points = np.array([(int(p[0]), int(p[1])) for p in points])
    points = points * scale_factor
    points = points.astype(int)
    mask = cv2.drawContours(mask, [points], -1, color=color_, thickness=5)
    mask = cv2.fillPoly(mask, [points], color=color_)
    return mask

def parse_xml_file(cvat_xml, classname):
    root = etree.parse(cvat_xml).getroot()
    track = []
    track_name_attr = ".//track[@label='{}']".format(classname)
    for track_tag in root.iterfind(track_name_attr):
        for poly_tag in track_tag.iter('polygon'):
            polygon = {'type': 'polygon'}
            if poly_tag.attrib['outside'] == '0':
                for key, value in poly_tag.items():
                    polygon[key] = value
                track.append(polygon)

        # 按照 key=lambda x: int(x.get('z_order', 0)) 方式排序
        track.sort(key=lambda x: int(x.get('frame', 0)))
    return track


def create_mask_file(images_dir, output_dir, Boundary, Crop, scale_factor, color):
    img_list = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
    mask_bitness = 24
    for img in tqdm(img_list, desc="Writing contours:"):
        frame_name = str(int((img.split('.')[0]).split('_')[1]))
        img_path = os.path.join(images_dir, img)
        current_image = cv2.imread(img_path)
        height, width, _ = current_image.shape
        background = np.zeros((height, width, 3), np.uint8)
        output_path = os.path.join(output_dir, img.split('.')[0] + '.png')
        mask = np.full((height, width, mask_bitness // 8), background, dtype=np.uint8)

        for boundary in Boundary:
            if boundary["frame"] == frame_name:
                mask = mask_color(boundary, scale_factor, mask, color[1])
        for crop in Crop:
            if crop["frame"] == frame_name:
                mask = mask_color(crop, scale_factor, mask, color[0])
        cv2.imwrite(output_path, mask)


def parse_args():
    """
    # dir format:
    cvat_data:
     -- shuidaosuo01
        -- annotations.xml
        -- images
           -- frame_000000.PNG
           -- frame_000010.PNG
     -- shuidaosuo02
        -- annotations.xml
        -- images
           -- frame_000000.PNG
           -- frame_000010.PNG
    """
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@', description='Convert CVAT XML annotations to contours')
    parser.add_argument('--data_dir', metavar='', type=str, default="./cvat_data",
                        help='directory with input images')
    parser.add_argument('--color_flag', metavar='', type=str, default=True,
                        help='directory for output masks')
    parser.add_argument('--color', metavar='', type=list, default=[(0, 255, 0), (0, 0, 255)],
                        help='directory for output masks')
    parser.add_argument('--scale-factor', type=float, default=1.0,
                        help='choose scale factor for images')
    return parser.parse_args()


def main():
    args = parse_args()
    dir_list = [f for f in os.listdir(args.data_dir) if os.path.isdir(os.path.join(args.data_dir, f))]
    for dir in dir_list:
        dirpath = os.path.join(args.data_dir, dir)

        if args.color_flag:
            color = args.color
            output_dir = os.path.join(dirpath, 'masks_color')
        else:
            output_dir = os.path.join(dirpath, 'masks')
            color = [(1, 1, 1), (2, 2, 2)]

        # 解析 .xml 文件，得到各个类别下的frame信息,列表格式
        cvat_xml = os.path.join(dirpath, 'annotations.xml')
        Crop = parse_xml_file(cvat_xml, 'field with crop')
        Boundary = parse_xml_file(cvat_xml, 'field boundary')

        # 画出masks
        images_dir = os.path.join(dirpath, 'images')
        dir_create(output_dir)
        create_mask_file(images_dir, output_dir, Boundary, Crop, args.scale_factor, color)


if __name__ == "__main__":
    main()
