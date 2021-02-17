# -*- coding:utf-8 -*-
'''
主要功能：通过样本点的经纬度坐标来提取栅格图像中的样本点
输入：投影坐标
输出：DN值
1）读取TIF图像的各个参数，并返回值；
2）提取过程；
3）输出；
@ author:zhyin
@ time:2019/09/16
'''

import gdal
import osr
import numpy as np
import os
import time


def get_file_info(rs_file_path):
    '''
    打开栅格图像文件

    :param rs_file_path:输入的文件路径
    :return: gdal数据集、地理空间坐标系、投影坐标系、栅格影像的大小等相关信息
    '''

    # 定义变量
    pcs = None  # 投影坐标系
    gcs = None  # 地理坐标系
    shape = None  # 定义图像的大小

    if rs_file_path.endswith(".tif") or rs_file_path.endswith(".TIF"):
        dataset = gdal.Open(rs_file_path)
        pcs = osr.SpatialReference()
        pcs.ImportFromWkt(dataset.GetProjection())
        #
        gcs = pcs.CloneGeogCS()
        #
        extend = dataset.GetGeoTransform()
        #
        shape = (dataset.RasterXSize, dataset.RasterYSize)
    else:
        raise ("Unsorport file format")
    #
    return dataset, pcs, gcs, extend, shape


def lonlat_to_xy(gcs, pcs, lon, lat):
    '''
    经纬度坐标转换为投影坐标

    :param gcs: 地理空间坐标信息，可以由get_file_info()函数直接获取
    :param pcs: 投影坐标信息，可以由get_file_info()函数直接获取
    :param lon: 经度坐标
    :param lat: 纬度坐标
    :return: 地理空间坐标对于的投影坐标
    '''

    #
    ct = osr.CoordinateTransformation(gcs, pcs)
    coordinates = ct.TransformPoint(lon, lat)
    #
    return coordinates[0], coordinates[1], coordinates[2]


def xy_to_lonlat(gcs, pcs, x, y):
    '''
    投影坐标转换为经纬度坐标

    :param gcs: 地理空间坐标信息，可以由get_file_info()函数直接获取
    :param pcs: 投影坐标信息，可以由get_file_info()函数直接获取
    :param x: 像元的行号
    :param y: 像元的列号
    :return: 投影坐标对于的地理空间坐标
    '''

    #
    ct = osr.CoordinateTransformation(pcs, gcs)
    lon, lat, _ = ct.TransformPoint(x, y)
    #
    return lon, lat


def xy_to_rowcol(extend, x, y):
    '''
    根据gdal的六参数模型将给定的投影坐标转换为影像图上坐标（行列号）

    :param extend: 图像的空间范围
    :param x: 投影坐标x
    :param y: 投影坐标y
    :return: 投影坐标（x,y）对应的影像图上行列号（row,col）
    '''

    a = np.array([[extend[1], extend[2]], [extend[4], extend[5]]])
    b = np.array([x - extend[0], y - extend[3]])
    #
    row_col = np.linalg.solve(a, b)
    row = int(np.floor(row_col[1]))
    col = int(np.floor(row_col[0]))
    #
    return row, col


def rowcol_to_xy(extend, row, col):
    '''
    根据gdal的六参数模型将给定的影像图上坐标（行列号）转为投影坐标系或地理坐标系

    :param extend:图像的空间范围
    :param row:像元的行号
    :param col:像元的列号
    :return:行列号（row,col）对应的投影坐标（x,y）
    '''
    #
    x = extend[0] + row * extend[1] + col * extend[2]
    y = extend[3] + row * extend[4] + col * extend[5]
    #
    return x, y


def get_value_by_coordinates(file_path, coordinates, coordinates_type="rowcol"):
    '''
    直接根据图像坐标，或者依据GDAL的六参数模型将给定的投影、地理坐标转为影像图上坐标后，返回对应像元的像元值

    :param file_path: 图像文件的路径
    :param coordinates: 坐标，2个元素的元组，坐标可以设置为如下的三种：像元的行列号，投影坐标或者地理空间坐标
    :param coordinates_type: 坐标类型，"rowcol"、"xy"、"lonlat"
    :return: 制定坐标的像元值
    '''

    #
    dataset, gcs, pcs, extend, shape = get_file_info(file_path)
    img = dataset.GetRasterBand(1).ReadAsArray()
    value = None
    #
    if coordinates_type == "rowcol":
        value = img[coordinates[0], coordinates[1]]
    elif coordinates_type == "lonlat":
        x, y, _ = lonlat_to_xy(gcs, pcs, coordinates[0], coordinates[1])
        row, col = xy_to_rowcol(extend, x, y)
        value = img[row, col]
    elif coordinates_type == "xy":
        row, col = xy_to_rowcol(extend, coordinates[0], coordinates[1])
        value = img[row, col]
    else:
        raise ('''"coordinates_type":Wrong parameter input''')
    #
    return value


def get_xy_txt(txt_file_path, train_total, test_total):
    '''
    获取样本点的投影坐标x,y
    :param txt_file_path: 存储训练样本和测试样本的投影坐标的txt文件
    :param train_total: 训练样本的总个数
    :param test_total: 测试样本的总个数
    :return: 投影坐标（x,y）
    '''
    #
    train_sample_tuple = []
    test_sample_tuple = []
    #
    txt_read = open(txt_file_path, 'r')
    #
    train_flag = False
    test_flag = False
    train_num = 0
    test_num = -2
    # 开始读取txt文件
    while True:
        content_line = txt_read.readline().split()

        if not content_line:
            break
            pass

        # 储存训练数据的投影坐标
        if content_line[0] == "1":
            train_flag = True
            test_num += 1
        if train_num >= 0 and train_num < train_total and train_flag == True:
            train_sample_tuple.append([content_line[1], content_line[2]])
            train_num += 1
        if train_num == train_total:
            train_flag = False
        # 储存测试数据的投影坐标
        if test_num == 0:
            test_flag = True
        if test_num >= 0 and test_num < test_total and test_flag == True:
            test_sample_tuple.append(([content_line[1], content_line[2]]))
            test_num += 1
        if test_num == test_total:
            test_flag = False

    # 从list转换为array.float类型
    train_sample_tuple = np.array(train_sample_tuple).astype(float)
    test_sample_tuple = np.array((test_sample_tuple)).astype(float)
    #
    return train_sample_tuple, test_sample_tuple


def walk_tiff(input_dir):
    '''
    遍历文件，寻找TIF文件，并记录文件名在这里主要是遍历当前文件夹。

    :param input_dir: 目标文件夹
    :return: 包含所有TIF文件的列表path_tiffs
    '''
    path_tiffs = []
    #
    for roots, dirs, files in os.walk(input_dir):
        for dir in dirs:
            if "LC08" in dir:
                tif_dir = ("%s%s/" % (input_dir, dir))
                tif_names = [("%s_B1.TIF" % dir[-40:]), ("%s_B2.TIF" % dir[-40:]),
                             ("%s_B3.TIF" % dir[-40:]), ("%s_B4.TIF" % dir[-40:]),
                             ("%s_B5.TIF" % dir[-40:]), ("%s_B6.TIF" % dir[-40:]),
                             ("%s_B7.TIF" % dir[-40:])]
                #
                for tif_name in tif_names:
                    path_tiff = os.path.join(tif_dir, tif_name)
                    path_tiffs.append(path_tiff)
    return path_tiffs


def batch_sampling(rs_rootdir, samplexy_filedir, dn_rootdir,
                   train_samplenum, test_samplenum, band_num):
    '''
    主要功能：实现文件夹TIF文件的批采样，将样本点数据以TXT文件的格式进行保存

    :param rs_rootdir: 遥感影像文件存放根目录
    :param samplexy_filedir: 存放有样本点的文件目录
    :param dn_rootdir: 需要写入DN值的TXT文件的
    :param train_samplenum: 训练样本点的数目
    :param test_samplenum: 测试样本点数目
    :param band_num: 遥感影像的波段数
    :return: 没有返回值，将文件写入工作
    '''

    # 遍历文件夹
    dir = rs_rootdir
    path_tiffs = walk_tiff(dir)

    # 获取样本点的UTM16N投影坐标
    train_xy_tuple, test_xy_tuple = get_xy_txt(samplexy_filedir,
                                               train_samplenum,
                                               test_samplenum)

    #
    flag1 = 0  # 设置一个计数器，记录波段数
    flag2 = 0  # 设置计数器，记录样本数

    # 设置交互：询问需要导入什么数据
    category = input("which kind of crop you want to input:\n")
    mode = input("train mode or test mode ??? formate:train/test\n")

    # 储存像元的DN值
    # 打开文件并记录文件头
    f = open(("%s/%s_%s_DN.txt" % (dn_rootdir, category, mode)), 'w')
    header = ("; @author: zhyin\n; @time: %s\n; %s_%s_sample:\n \t\tB1\tB2\tB3\tB4\tB5\tB6\tB7\n" % (
        time.ctime(), category, mode))
    f.write(header)

    # 读取坐标值，并写入TXT文件
    if mode == "train":
        for xy in train_xy_tuple:
            # 样本点记录
            flag1 += 1
            f.write("\nsample %s :" % str(flag1))
            #
            for path_tiff in path_tiffs:
                _, gcs, pcs, extend, _ = get_file_info(path_tiff)
                pixel_value1 = get_value_by_coordinates(path_tiff, xy, coordinates_type="xy")

                # 对每一个样本的值进行记录
                flag2 += 1
                if (flag2 % band_num == 1):
                    f.write("\n\t%s: " % path_tiff[-30:-22])
                f.write("%s\t" % pixel_value1)
        # 关闭文件
        f.close()
    #
    if mode == "test":
        for xy in test_xy_tuple:
            # 样本点记录
            flag1 += 1
            f.write("\nsample %s :" % str(flag1))
            #
            for path_tiff in path_tiffs:
                _, gcs, pcs, extend, _ = get_file_info(path_tiff)
                pixel_value1 = get_value_by_coordinates(path_tiff, xy, coordinates_type="xy")

                # 对每一个样本的值进行记录
                flag2 += 1
                if (flag2 % band_num == 1):
                    f.write("\n\t%s: " % path_tiff[-30:-22])
                f.write("%s\t" % pixel_value1)

        # 关闭文件
        f.close()
