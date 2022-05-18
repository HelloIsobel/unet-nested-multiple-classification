import os, shutil

check_dir = lambda d: None if os.path.exists(d) else os.makedirs(d)

# path = "./data/output_resize/"
# path1=r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\output_resize"
# outputdir=r"D:\Desktop\GitHub\Boundary_rice\Network\unet-nested-multiple-classification\data\test\output"

path1="../data/output_resize/"
outputdir="../data/test/output/"
check_dir(outputdir)
i = 1
for root, dirs, files in os.walk(path1):
    for file in files:
        filepath = os.path.join(root, file)
        outpath = os.path.join(outputdir, file)
        shutil.copy(filepath, outpath)
        print("【{}】{}".format(i, file))
        i = i + 1
