"""
将images/masks 文件修改名称
保存到统一一个文件夹下

有时间用下面函数改下：
images = glob.glob('data/*/images/*.jpg')
"""


import os

check_dir = lambda d: None if os.path.exists(d) else os.makedirs(d)

path = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\cvat_data_final"
images_outdirpath = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\images"
masks_outdirpath = r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\masks"
check_dir(images_outdirpath)
check_dir(masks_outdirpath)

for task in os.listdir(path):
    if "_" in task:
        task_name = task.split("_")[0]
    else:
        task_name = task

    taskdir = os.path.join(path, task)

    imagedir = os.path.join(taskdir, "images_resize")
    for item in os.listdir(imagedir):
        # print('item name is ',item)
        name = item.split('.', 1)[0]
        src = os.path.join(imagedir, item)
        dst = os.path.join(images_outdirpath, task_name + "_" + name + '.png')
        try:
            os.rename(src, dst)
            print('rename from %s to %s' % (src, dst))
        except:
            continue

    maskdir = os.path.join(taskdir, "masks_resize")
    for item in os.listdir(maskdir):
        # print('item name is ',item)
        name = item.split('.', 1)[0]
        src = os.path.join(maskdir, item)
        dst = os.path.join(masks_outdirpath, task_name + "_" + name + '.png')
        try:
            os.rename(src, dst)
            print('rename from %s to %s' % (src, dst))
        except:
            continue

