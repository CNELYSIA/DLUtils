import random

import cv2
import numpy as np
import ogr
import gdal
import os
from itertools import groupby
from skimage import morphology


# 排序器
def Sort_Key(item):
    G = int(item[:3])
    H = int(item[3:6])
    W = int(item[6:9])
    return G, H, W


def _Transform(oriPath, Reference):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    SHP = driver.Open(oriPath)
    SHP_NAME = oriPath.split('\\')[-1].split('.')[0]
    SHP_LAYER = SHP.GetLayer()
    layer_extent = SHP_LAYER.GetExtent()
    min_x = layer_extent[0]
    max_x = layer_extent[1]
    min_y = layer_extent[2]
    max_y = layer_extent[3]

    IMG = gdal.Open(Reference)
    width = IMG.RasterXSize
    height = IMG.RasterYSize

    IMAGE = np.zeros((height, width, 3), np.uint8)
    for feature in SHP_LAYER:
        geometry = feature.GetGeometryRef()
        # 获取要素的几何类型
        geom_type = geometry.GetGeometryType()

        # 获取要素的坐标
        if geom_type == ogr.wkbPoint:
            x, y = geometry.GetX(), geometry.GetY()
            # 将要素的坐标转换为图像坐标
            img_x = int((x - min_x) / (max_x - min_x) * width)
            img_y = int((y - min_y) / (max_y - min_y) * height)
            # 在图像上绘制点
            cv2.circle(IMAGE, (img_x, img_y), 3, (255, 255, 255), -1)

        elif geom_type == ogr.wkbLineString:
            # 获取线的坐标点
            line = geometry.GetPoints()
            # 将线的坐标点转换为图像坐标
            img_points = []
            for point in line:
                x, y = point[0], point[1]
                img_x = int((x - min_x) / (max_x - min_x) * width)
                img_y = int((y - min_y) / (max_y - min_y) * height)
                img_points.append((img_x, img_y))
            # 在图像上绘制线
            cv2.polylines(IMAGE, [np.array(img_points)], False, (255, 255, 255), 2)

        elif geom_type == ogr.wkbPolygon:
            # 获取多边形的外环坐标点
            ring = geometry.GetGeometryRef(0)
            points = ring.GetPoints()
            # 将多边形的坐标点转换为图像坐标
            img_points = []
            for point in points:
                x, y = point[0], point[1]
                img_x = int((x - min_x) / (max_x - min_x) * width)
                img_y = int((y - min_y) / (max_y - min_y) * height)
                img_points.append((img_x, img_y))
            # 在图像上绘制多边形
            cv2.polylines(IMAGE, [np.array(img_points)], True, (255, 255, 255), 2)
            cv2.fillPoly(IMAGE, [np.array(img_points)], (255, 255, 255))

    SHP_DICT = {SHP_NAME: IMAGE}
    return SHP_DICT


def ReadSHP(oriPath, Reference):
    SHP_LIST = []
    if os.path.isfile(oriPath):
        SHP_LIST = Pack(_Transform(oriPath, Reference))
    elif os.path.isdir(oriPath):
        List = os.listdir(oriPath)
        for item in List:
            if item.split('.')[-1] == 'shp':
                item = os.path.join(oriPath, item)
                SHP_LIST.append(_Transform(item, Reference))
    return SHP_LIST


# 读取图片，返回list
def ReadIMG(oriPath):
    IMAGE_DICT = {}
    if os.path.isfile(oriPath):
        IMG_NAME = oriPath.split('\\')[-1].split('.')[0]
        IMAGE = cv2.imread(oriPath)
        IMAGE_DICT.update({IMG_NAME: IMAGE})
    elif os.path.isdir(oriPath):
        List = os.listdir(oriPath)
        for item in List:
            item = os.path.join(oriPath, item)
            IMG_NAME = item.split('\\')[-1].split('.')[0]
            IMAGE = cv2.imread(item)
            IMAGE_DICT.update({IMG_NAME: IMAGE})
    IMAGE_LIST = Pack(IMAGE_DICT)
    return IMAGE_LIST


def Pack(keyValues):
    if isinstance(keyValues, list):
        return keyValues
    if isinstance(keyValues, dict):
        List = [keyValues]
        return List


def Save(keyValues, outPath, outFormat='png'):
    outPath = os.path.join(outPath, '')
    keyValues = Pack(keyValues)
    for keyValue in keyValues:
        IMG_NAMES = list(keyValue.keys())
        for IMG_NAME in IMG_NAMES:
            cv2.imwrite('{}\\{}.'.format(outPath, IMG_NAME) + outFormat, keyValue.get(IMG_NAME))


# 迭代器，用于批量处理同目录多个文件,返回装有字典的列表
def Iter(list, func, **params):
    outPut = []
    for item in list:
        outPut.append(func(item, **params))
    PreProcess.GROUP = 1
    return outPut


# 预处理类，负责数据预处理相关操作
class PreProcess:
    GROUP = 1

    # 影像裁剪
    @classmethod
    def IMG_Crop(cls, keyValues, W=512, H=512, Step=256):
        keyValues = Pack(keyValues)
        IMG_DICT = {}
        IMG_LIST = []
        IMG_H = 1
        IMG_W = 1
        for keyValue in keyValues:
            IMG_NAMES = list(keyValue.keys())
            for IMG_NAME in IMG_NAMES:
                IMAGE = keyValue.get(IMG_NAME)
                size = IMAGE.shape
                i = 0
                for _H in range(0, size[0], Step):
                    START_H = _H  # START_H表示起始高度，从0以步长Step=256开始循环
                    for _W in range(0, size[1], Step):
                        START_W = _W  # START_W表示起始宽度，从0以步长Step=256开始循环
                        END_H = START_H + H  # END_H是终止高度

                        if END_H > size[0]:  # 如果边缘位置不够512的列
                            # 以倒数512形成裁剪区域
                            START_H = size[0] - H
                            END_H = START_H + H
                            i = i - 1
                        END_W = START_W + W  # END_W是中止宽度
                        if END_W > size[1]:  # 如果边缘位置不够512的行
                            # 以倒数512形成裁剪区域
                            START_W = size[1] - W
                            END_W = START_W + W
                            i = i - 1

                        Crop = IMAGE[START_H:END_H, START_W:END_W]  # 执行裁剪操作
                        i = i + 1
                        NAME_IMG = str(PreProcess.GROUP).zfill(3) + str(IMG_H).zfill(3) + str(IMG_W).zfill(
                            3)  # 用起始坐标来命名切割得到的图像，为的是方便后续标签数据抓取
                        IMG_DICT[NAME_IMG] = Crop
                        IMG_W += 1
                    IMG_H += 1
                    IMG_W = 1
                PreProcess.GROUP += 1
        return IMG_DICT

    @staticmethod
    def Balance(imgKeyValues, labKeyValues, ratio=1):
        ALL_BLACK = []
        for labkeyValue in labKeyValues:
            IMG_NAMES = list(labkeyValue.keys())
            for IMG_NAME in IMG_NAMES:
                if cv2.countNonZero(cv2.cvtColor(labkeyValue.get(IMG_NAME), cv2.COLOR_BGR2GRAY)) == 0:
                    ALL_BLACK.append(IMG_NAME)
        Ratio_Total = int(len(ALL_BLACK) * ratio)
        ALL_BLACK = ALL_BLACK[:Ratio_Total]
        random.shuffle(ALL_BLACK)
        for labkeyValue, imgkeyValue in zip(labKeyValues, imgKeyValues):
            for Black in ALL_BLACK:
                labkeyValue.pop(Black)
                imgkeyValue.pop(Black)
        return labKeyValues, imgKeyValues


class PostProcess:
    # 去除噪点
    @staticmethod
    def NoiseReduction(keyValues, kernelSize=3, **params):
        DICT = {}
        keyValues = Pack(keyValues)
        for keyValue in keyValues:
            IMG_NAMES = list(keyValue.keys())
            for IMG_NAME in IMG_NAMES:
                Median = keyValue.get(IMG_NAME)
                Median = cv2.medianBlur(Median, kernelSize)
                Median = np.array(Median, dtype=bool)
                IMAGE = morphology.remove_small_objects(Median, **params)
                IMAGE = np.array(IMAGE, dtype=int)
                IMAGE *= 255
                DICT.update({IMG_NAME: IMAGE})
        return DICT

    # 多模型结果合并
    # 图像叠加
    @staticmethod
    def IMG_Combine(images, labels, alpha=0.5):
        images = Pack(images)
        labels = Pack(labels)
        DICT = {}
        for image, label in zip(images, labels):
            IMG_NAMES = list(image.keys())
            for IMG_NAME in IMG_NAMES:
                Combine = cv2.addWeighted(image.get(IMG_NAME), alpha, label.get(IMG_NAME), 1 - alpha, 0, dtype=cv2.CV_64F)
                DICT.update({IMG_NAME: Combine})
        return DICT

    @classmethod
    def IMG_Restore(cls, keyValues):
        keyValues = Pack(keyValues)
        Horizontal = []
        Vertical = []
        IMG_DICT = {}
        for keyValue in keyValues:
            IMG_NAMES = list(keyValue.keys())
            IMG_NAMES = sorted(IMG_NAMES, key=Sort_Key)
            IMG_NAMES = [[list(group) for _, group in groupby(Col, key=lambda x: x[3:6])] for _, Col in
                         groupby(IMG_NAMES, key=lambda x: x[:3])]
            for G in range(len(IMG_NAMES)):
                for H in range(len(IMG_NAMES[G])):
                    for IMG_NAME in IMG_NAMES[G][H]:
                        Horizontal.append(keyValue.get(IMG_NAME))
                    Vertical.append(cv2.hconcat(Horizontal))
                    Horizontal.clear()
                Restore = cv2.vconcat(Vertical)
                Vertical.clear()
                IMG_DICT[IMG_NAME] = Restore
        IMG_DICT = Pack(IMG_DICT)
        return IMG_DICT
