# DLUtils
一个用于深度学习数据处理的工具类(渣作)


ReadSHP(oriPath, Reference) oriPath：目录或文件均可 参考栅格（用于确定投影和影像大小） 此方法可用于将shp文件转换为png等格式的图片：使用此方法读取后使用Save保存即可

ReadIMG(oriPath) oriPath：目录或文件均可

Save(keyValues, outPath, outFormat='png') keyValues：字典{图片名： 图片}或列表（使用ReadIMG/SHP默认获取此形式数据） outPath：输出路径 outFormat：输出格式 程序中想要保存文件须通过此方法，之前使用目录作为每个方法的参数时感觉很乱QAQ

Iter(list, func, **params) 用方法做参数的迭代器，目前仅能配合crop使用实现一个目录下多个图像裁剪并分组命名

IMG_Crop(cls, keyValues, W=512, H=512, Step=256) keyValues：字典{图片名： 图片}或列表（使用ReadIMG/SHP默认获取此形式数据） W:裁剪后宽 H：裁剪后高 Step：重叠区域，不想重叠设为512

Balance(imgKeyValues, labKeyValues, ratio=1) 清除全黑样本 imgKeyValues：图片，使用ReadIMG读取 labKeyValues：标签，使用ReadIMG读取 ratio调整保留比例，1表示不保留全黑样本

NoiseReduction(keyValues, kernelSize=3, **params) 去除噪点（要求图片为二值图片） kernelSize=3 滤波核 大于1的奇数 **params：min_size = 64, connectivity = 1, 连通区，默认64，小于64被清除， connectivity 1为4连通，2为8连通

IMG_Combine(images, labels, alpha=0.5) 图像融合 alpha为透明度

IMG_Restore(cls, keyValues) 将crop裁剪的图像进行拼接，可使用ReadIMG读取某一目录下的图片

自己写的辣鸡东东，如果有大佬有好的建议或者是发现程序里面有问题的话还请指正OwO
