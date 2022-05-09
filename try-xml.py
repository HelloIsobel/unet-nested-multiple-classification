
from xml.etree.ElementTree import parse

tree = parse('annotations.xml')  # 获取ElementTree
root = tree.getroot()   # 获取根元素
anno = []
image_name_attr = ".//polygon[@frame='{}']".format('1900')
for image_tag in root.iterfind(image_name_attr):
    image = {}
    for key, value in image_tag.items():
        image[key] = value
    anno.append(image)
print(1)


# for child in root:
#     a=child.attrib
#     if a:
#         b=a['label']
#         print(b)
#     # print(child.tag, child.attrib)
#     # print(child.attrib)

