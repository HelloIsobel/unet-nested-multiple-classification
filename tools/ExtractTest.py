import os, random, shutil
import datetime


def moveFile(fileDir, tarDir):
    pathDir = os.listdir(fileDir)  # 取图片的原始路径
    filenumber = len(pathDir)
    rate = 0.1  # 自定义抽取图片的比例，比方说100张抽10张，那就是0.1
    picknumber = int(filenumber * rate)  # 按照rate比例从文件夹中取一定数量图片
    sample = random.sample(pathDir, picknumber)  # 随机选取picknumber数量的样本图片
    # print(sample)
    print(len(sample))
    for name in sample:
        shutil.move(fileDir + name, tarDir + name)
        shutil.move("./data/masks/"+name, './data/test/masks/'+name)



if __name__ == '__main__':
    check_dir = lambda d: None if os.path.exists(d) else os.makedirs(d)

    fileDir = "./data/images/"  # 源图片文件夹路径
    tarDir='./data/test/images/'  # 移动到新的文件夹路径
    check_dir(tarDir)

    moveFile(fileDir, tarDir)
    timenow=datetime.datetime.now()
    print(timenow)