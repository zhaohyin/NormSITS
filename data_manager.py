# -*- coding:utf-8 -*-
'''
实现对遥感数据的管理：
1. 数据获取：1）连接google storage的数据库 ；2）获取感兴趣区域的遥感影像；3）调用IDM下载遥感影像
2. 数据管理：1) 获取下载影像的RGB真彩色合成图片，有一个直观的印象
@ author: zhyin
@ time: 2019/10/12
'''

from osgeo import gdal
from pyhdf.SD import SD, SDC  # conda install -c conda-forge pyhdf
import os, osr, scipy.io
import numpy as np
import pixel_extract as pext
import time, math
import gdal
import matplotlib.pyplot as plt
import pandas as pd


class dataManagement(object):
    def __init__(self):
        self.sample_num = 0

    def linearstretching(self, img):

        min = np.percentile(img, 1)
        max = np.percentile(img, 99)
        img = np.where(img > min, img, min)
        img = np.where(img < max, img, max)
        img = (img - min) / (max - min) * 255
        return img


class landsatData(object):
    '''
    存储Landsat数据相关的操作，包括数据下载，
    '''

    def _readImg(self, filedir):
        '''
        读取影像
        '''
        dataset = gdal.Open(filedir)  # 打开文件

        width = dataset.RasterXSize  # 栅格矩阵的列数
        height = dataset.RasterYSize  # 栅格矩阵的行数

        gcs = dataset.GetGeoTransform()  # 仿射矩阵
        pcs = dataset.GetProjection()  # 地图投影信息
        data = dataset.ReadAsArray(0, 0, width, height)  # 将数据写成数组，对应栅格矩阵

        del dataset  # 关闭对象，文件dataset
        return pcs, gcs, data, width, height

    def _rgbCombination(self, gtiff_name, R_DIR, G_DIR, B_DIR, LM='Rapid'):
        #
        # 读取每个TIF
        pcs, gcs, Bdata, width, height = self._readImg(B_DIR)
        _, _, Gdata, _, _ = self._readImg(G_DIR)
        _, _, Rdata, _, _ = self._readImg(R_DIR)
        #
        # 线性拉伸
        if LM == 'Slow':
            Bdata = self._percentCut(Bdata, 2, 98)
            Gdata = self._percentCut(Gdata, 2, 98)
            Rdata = self._percentCut(Rdata, 2, 98)
        if LM == 'Rapid':
            Bdata = dataManagement().linearstretching(Bdata)
            Gdata = dataManagement().linearstretching(Gdata)
            Rdata = dataManagement().linearstretching(Rdata)
        #
        # 定义输出TIFF的格式
        gtiff_driver = gdal.GetDriverByName('GTiff')
        # gtiff_name = "./datasat/%s_%s%s%s.tif" % (B_DIR[-47:-7],R_DIR[-5],G_DIR[-5],B_DIR[-5])
        out_ds = gtiff_driver.Create(gtiff_name,
                                     width,
                                     height,
                                     3,
                                     gdal.GDT_Byte)
        out_ds.SetProjection(pcs)
        out_ds.SetGeoTransform(gcs)
        #
        # 存入1波段数据
        out_ds.GetRasterBand(3).WriteArray(Bdata)
        #
        # 存入2波段数据
        out_ds.GetRasterBand(2).WriteArray(Gdata)
        #
        # 存入3波段数据
        out_ds.GetRasterBand(1).WriteArray(Rdata)

        out_ds.FlushCache()
        #
        del out_ds
        #
        # return gtiff_name

    def _bandCombination(self, RS_dir):
        '''
        754假彩色合成
        :param dir: 遥感影像存放目录
        :param path: 遥感影像的行
        :param row: 遥感影像的列
        :return: RGB png格式图片
        '''
        # 遍历文件夹，逐个进行RGB图像合成
        for roots, dirs, files in os.walk(RS_dir):
            #
            # 规定读取顺序
            order_list = ['LTCP0123456789_']
            someorder = {letter: val for val, letter in enumerate(order_list[0])}
            new_dirs = sorted(dirs, key=lambda x: [someorder.get(letter) for letter in x])
            #
            for dir in new_dirs:
                if "L" in dir:
                    tif_dir = "%s%s/" % (RS_dir, dir)
                    tif_name = [("%s_B4.TIF" % dir[-40:]),
                                ("%s_B5.TIF" % dir[-40:]),
                                ("%s_B7.TIF" % dir[-40:])]
                    band_tif1 = os.path.join(tif_dir, tif_name[0])
                    band_tif2 = os.path.join(tif_dir, tif_name[1])
                    band_tif3 = os.path.join(tif_dir, tif_name[2])
                    #
                    # 读取每个TIF
                    pcs, gcs, Bdata, width, height = self._readImg(band_tif1)
                    _, _, Gdata, _, _ = self._readImg(band_tif2)
                    _, _, Rdata, _, _ = self._readImg(band_tif3)
                    #
                    # 线性拉伸
                    Bdata = self._percentCut(Bdata, 2, 98)
                    Gdata = self._percentCut(Gdata, 2, 98)
                    Rdata = self._percentCut(Rdata, 2, 98)

                    #
                    # 定义输出TIFF的格式
                    gtiff_driver = gdal.GetDriverByName('GTiff')
                    gtiff_name = "%s%s_754.tif" % (RS_dir, dir[-40:])
                    print(gtiff_name)
                    out_ds = gtiff_driver.Create(gtiff_name,
                                                 width,
                                                 height,
                                                 3,
                                                 gdal.GDT_Byte)
                    out_ds.SetProjection(pcs)
                    out_ds.SetGeoTransform(gcs)
                    #
                    # 存入1波段数据
                    out_ds.GetRasterBand(3).WriteArray(Bdata)
                    #
                    # 存入2波段数据
                    out_ds.GetRasterBand(2).WriteArray(Gdata)
                    #
                    # 存入3波段数据
                    out_ds.GetRasterBand(1).WriteArray(Rdata)

                    out_ds.FlushCache()
                    #
                    del out_ds

    def _tiffClip(self, TiffDir, Center_Lon, Center_Lat, Radius):
        '''
        目的：对TIFF数据进行裁剪，获取值并保存
        :param tiffDir: TIFF数据的地址
        :return: clipValue [2R+1,2R+1]
        '''
        # 初始化变量
        clipValue = []
        center_lon = float(Center_Lon)
        center_lat = float(Center_Lat)
        radius = int(Radius)
        #
        # 读取图片信息
        dataset = gdal.Open(TiffDir)
        extend = dataset.GetGeoTransform()
        pcs = dataset.GetProjection()
        sr = osr.SpatialReference()
        sr.ImportFromWkt(pcs)
        gcs = sr.CloneGeogCS()
        #
        # 辐射校正
        values = dataset.ReadAsArray().astype(float)
        multiple_reflectence = 2e-5
        add_reflectance = - 0.1
        values = multiple_reflectence * values + add_reflectance   # 这里计算的是 TOA planetary reflectance
        #
        x, y, _ = pext.lonlat_to_xy(gcs, sr, center_lon, center_lat)
        center_row, center_col = pext.xy_to_rowcol(extend, x, y)
        clipValue = np.array(values)[(center_row - radius):(center_row + radius+1),(center_col - radius):(center_col + radius+1)]
        print(center_row,center_col)
        return clipValue
        pass

    def _pixExtract(self, roi_lonlats, RS_dir, Band, Radius='1', Filter='Mean'):
        '''
        获取感兴趣点的时间序列曲线
        :param lon: 感兴趣点的经度
        :param lat: 感兴趣点的纬度
        :param band: 需要什么波段的数据
        :return:
        '''
        #
        pix_value = []
        lonlats = np.array(roi_lonlats).astype(float)
        rowcols = []
        radius = int(Radius)
        #
        # 遍历文件夹，找出所有的该波段的图像
        for roots, dirs, files in os.walk(RS_dir):
            #
            # 规定读取顺序
            order_list = ['LTCP0123456789_t']
            someorder = {letter: val for val, letter in enumerate(order_list[0])}
            new_dirs = sorted(dirs, key=lambda x: [someorder.get(letter) for letter in x])
            #
            for dir in new_dirs:
                if "L" in dir:
                    tif_dir = "%s%s/" % (RS_dir, dir)
                    tif_name = "%s_%s.TIF" % (dir[-40:], Band)
                    tiff_path = os.path.join(tif_dir, tif_name)
                    dataset = gdal.Open(tiff_path)
                    #
                    # 加载投影信息
                    extend = dataset.GetGeoTransform()  # 仿射矩阵
                    pcs = dataset.GetProjection()  # 地图投影信息
                    sr = osr.SpatialReference()
                    sr.ImportFromWkt(pcs)
                    gcs = sr.CloneGeogCS()
                    #
                    # 辐射校正
                    values = dataset.ReadAsArray().astype(float)
                    multiple_reflectence = 2e-5
                    add_reflectance = - 0.1
                    values = multiple_reflectence * values + add_reflectance
                    #
                    # 获取所有样本点在同一个影像的波段值
                    time_value = []
                    for i in range(len(lonlats)):
                        #
                        x, y, _ = pext.lonlat_to_xy(gcs, sr, lonlats[i, 0], lonlats[i, 1])
                        row, col = pext.xy_to_rowcol(extend, x, y)
                        if i == (len(lonlats) - 1) / 2:
                            rowcols.append([row, col])
                        #
                        # 确定取值的方法：None，Max or Mean
                        if radius == 0:
                            time_value.append(np.round(values[row, col], 3))
                        else:
                            #
                            # 将样本点周围像元进行合并
                            flag1_pix = []  # 过渡变量
                            for bios_row in range(-radius, radius + 1):
                                for bios_col in range(-radius, radius + 1):
                                    flag1_pix.append(np.round(values[row + bios_row, col + bios_col], 3))  # [9,]
                            #
                            if Filter == 'Max':
                                time_value.append(np.round(np.max(flag1_pix), 3))  # extend是一个一个的加入
                                # print(pix_value)
                            if Filter == 'Mean':
                                time_value.append(np.round(np.mean(flag1_pix), 3))  # extend是一个一个的加入
                                # print(pix_value)
                            if Filter == 'None':
                                time_value.append(np.round(values[row, col], 3))  # 单个点在该时间的数值
                    pix_value.append(time_value)
            #
        print(np.shape(pix_value))
        return pix_value
        pass

    def _ndviExtract(self, roi_lonlats, RS_dir):
        #
        pix_value = []
        lonlats = np.array(roi_lonlats).astype(float)
        #
        pix_value_B4 = self._pixExtract(lonlats, RS_dir, Band='B4', Radius='0')  # list:21*49
        pix_value_B5 = self._pixExtract(lonlats, RS_dir, Band='B5', Radius='0')
        #
        for i in range(np.shape(np.array(pix_value_B4))[1]):
            ndvi = (np.array(pix_value_B5)[:, i] - np.array(pix_value_B4)[:, i]) / (
                    np.array(pix_value_B5)[:, i] + np.array(pix_value_B4)[:, i])
            pix_value.append(ndvi)  # 49*21
        pix_value = np.transpose(pix_value)  # 21 * 49
        #
        return pix_value
        pass

    #
    # %%%%%%%%%%%%%%% 辅助算法 %%%%%%%%%%%%%%%%
    #
    def _histBuild(self, values) -> dict:
        '''
        影像直方图算法
        '''
        seq = values.flatten()
        hist = {}
        for i in seq:
            hist[i] = hist.get(i, 0) + 1
        return hist

    def _percentCut(self, values, left_percent=2, right_percent=2):
        '''
        伸缩变换,默认的去掉前2%和后2%的数据
        :param values: 图像值
        :param percent: 1-100
        :return: values(修改后) list:extend
        '''
        #
        hist = sorted(self._histBuild(values).items())

        # 初始化
        cum_hist = {}
        num = 0  # 总像元数
        max_value = 0  # 区域最大值
        min_value = 0  # 区域最小值
        last_key = 0  # 中间变量
        #
        # 累计分布直方图
        for value in hist:
            if value[0] == 0:
                cum_hist[value[0]] = value[1]
            else:
                cum_hist[value[0]] = cum_hist[last_key] + value[1]
            num += value[1]
            last_key = value[0]
        # print(num)
        #
        # 伸缩变换
        lower_num = int(num * left_percent / 100.0)
        upper_num = int(num * right_percent / 100.0)
        cumHist_sort = sorted(cum_hist.items())
        for value in cumHist_sort:
            if value[1] >= lower_num + cum_hist[0]:
                min_value = value[0]
                break
        for value in cumHist_sort:
            if value[1] >= upper_num:
                max_value = value[0]
                break
        # print(min_value,max_value)
        values = np.where(values > min_value, values, min_value)
        values = np.where(values < max_value, values, max_value)
        values = np.array((values - min_value) / float((max_value - min_value)) * 255).astype(int)
        return values
        pass

    def _doyAdd(self, pix_values=None, fig_saveDir="./mat/3_3-3069_2605-B1.mat"):
        '''
        测试程序,制作时间序列数据，并显示
        pix_values = scipy.io.loadmat("./mat/1_1-3071_2607-B7.mat")['time_sam']  # 21*49
        '''
        # pix_values = scipy.io.loadmat("./mat/3_3-3069_2605-B1.mat")['time_sam']  # 21*49
        max_values = np.max(np.array(pix_values))
        #
        doy = ['20171023', '20171108', '20171124', '20171210', '20171226', '20180111', '20180212',
               '20180316', '20180417', '20180503', '20180519', '20180604', '20180620', '20180823',
               '20180908', '20180924', '20181010', '20181026', '20181213', '20181229', '20190114']
        pix_values = np.array(pix_values)
        #
        # 画图
        fig = plt.figure(figsize=(16, 4))
        for i in range(np.shape(np.array(pix_values))[1]):
            df = pd.DataFrame({'doy': doy, 'value': pix_values[:, i]})
            df['doy'] = pd.to_datetime(df['doy'])
            plt.plot(df.doy, df.value)
            plt.scatter(df.doy, df.value, s=10)
        #
        ylabel = []
        for i in range(int(max_values / 0.05 + 3)):
            ylabel.append(0.05 * i)
        plt.xticks(doy, rotation=30, fontsize=6)
        plt.yticks(ylabel, fontsize=6)
        plt.title(fig_saveDir[-16:-4], fontsize=10)
        fig.savefig(fig_saveDir)
        # plt.show()

    def _lonlatAcquire(self, tiff_path, center_lon, center_lat, row_H, col_W):
        '''
        获取基准样本点周围的像元点，目的是为了测试白板的稳定性
        :param tiff_path: Landsat-8数据存放的地址
        :param center_lon: 基准样本点的经度
        :param center_lat: 基准样本点的纬度
        :param row_H: ROI采样的高半径
        :param col_W: ROI采样的宽半径
        :return: roi_lonlats list:point_num*2
        '''
        #
        # 初始化变量
        roi_lonlats = []
        roi_rowcols = []
        #
        dataset = gdal.Open(tiff_path)
        #
        # 加载投影信息
        extend = dataset.GetGeoTransform()  # 仿射矩阵
        pcs = dataset.GetProjection()  # 地图投影信息
        sr = osr.SpatialReference()
        sr.ImportFromWkt(pcs)
        gcs = sr.CloneGeogCS()
        #
        # 获取当前点的row,col
        x, y, _ = pext.lonlat_to_xy(gcs, sr, center_lon, center_lat)
        center_row, center_col = pext.xy_to_rowcol(extend, x, y)
        #
        # 获取周围点的lon,lat
        for row in range(center_row - row_H, center_row + row_H + 1):
            for col in range(center_col - col_W, center_col + col_W + 1):
                x, y = pext.rowcol_to_xy(extend, col, row)  ## 注意这里是COL，ROW
                lon, lat = pext.xy_to_lonlat(gcs, sr, x, y)
                roi_lonlats.append([lon, lat])
                roi_rowcols.append([row, col])
        #
        return roi_lonlats, roi_rowcols


class landsatMysqlDown(object):
    '''
    连接数据库进行Landsat数据下载
    '''

    def __init__(self):
        self.entity_dir = []
        self.file_url = []
        self.file_path = []

    def _connectSQL(self, csvDir='./index.csv'):
        #
        import mysql.connector
        # 连接数据库
        mydb = mysql.connector.connect(
            host="localhost",  # 数据库主机地址
            user="root",  # 数据库用户名
            passwd="960816",  # 数据库密码
        )
        mycursor = mydb.cursor()
        # mycursor.execute("DROP DATABASE landsat_index")  # 删除已有的数据库
        mycursor.execute("CREATE DATABASE landsat_index")  # 创建数据库
        mycursor.execute("USE landsat_index")

        # 生成表
        mycursor.execute("CREATE TABLE gc_index( sid INT UNSIGNED AUTO_INCREMENT, \
        	SCENE_ID VARCHAR(30),\
        	PRODUCT_ID VARCHAR(50),\
        	SPACECRAFT_ID VARCHAR(10),\
        	SENSOR_ID VARCHAR(10),\
        	DATE_ACQUIRED VARCHAR(10),\
        	COLLECTION_NUMBER VARCHAR(10),\
        	COLLECTION_CATEGORY VARCHAR(10),\
        	SENSING_TIME VARCHAR(30),\
        	DATA_TYPE VARCHAR(10),\
        	WRS_PATH INT,\
        	WRS_ROW INT,\
        	CLOUD_COVER FLOAT,\
        	NORTH_LAT FLOAT,\
        	SOUTH_LAT FLOAT,\
        	WEST_LON FLOAT,\
        	EAST_LON FLOAT,\
        	TOTAL_SIZE INT,\
        	BASE_URL VARCHAR(150),\
        	PRIMARY KEY ( sid ))DEFAULT CHARSET=utf8")

        # 查看表
        mycursor.execute("SHOW TABLES")
        for x in mycursor:
            print(x)

        # 查看描述
        mycursor.execute("desc gc_index")
        for x in mycursor:
            print(x)

        # 插入数据
        sql = "INSERT INTO gc_index (SCENE_ID,PRODUCT_ID,SPACECRAFT_ID,SENSOR_ID,DATE_ACQUIRED,COLLECTION_NUMBER,COLLECTION_CATEGORY,SENSING_TIME,DATA_TYPE,WRS_PATH,WRS_ROW,CLOUD_COVER,NORTH_LAT,SOUTH_LAT,WEST_LON,EAST_LON,TOTAL_SIZE,BASE_URL)\
                                   VALUES (%s,         %s,           %s,       %s,           %s,                %s,                %s,          %s,       %s,      %s,    %s,          %s,       %s,       %s,      %s,      %s,        %s,       %s)"

        # 得从第二行开始
        f = open(csvDir, 'r')
        lines = f.readlines()
        i = 0
        for line in lines:
            i += 1
            line = line.split(',')
            if i >= 2:
                mycursor.execute(sql, line)
        mydb.commit()

    def _saveURL(self, CLOUD_MAX=30, PATH=122, ROW=33, START_TIME='2017-10-07', END_TIME='2019-02-14',
                 SPACECRAFT='LANDSAT_8'):
        '''
        数据库匹配字段
        :param CLOUD_MAX: 最大云量
        :param PATH: 列号
        :param ROW: 行号
        :param START_TIME: 开始时间
        :param END_TIME: 结束时间,eg:'2020-10-20'
        :param SPACECRAFT: 传感器,eg:'LANDSAT_8'
        :return:
        '''
        #
        # 添加依赖库
        import mysql.connector
        import time
        import os
        self.entity_dir = []
        self.file_path = []
        self.file_url = []
        #
        #
        INFO = 'SCENE_ID, PRODUCT_ID,CLOUD_COVER,TOTAL_SIZE,BASE_URL'  # 保存的信息：产品ID，云量，大小，链接

        BASE_URL = 'http://storage.googleapis.com/'

        mydb = mysql.connector.connect(
            host="localhost",  # 数据库主机地址
            user="root",  # 数据库用户名
            passwd="960816",  # 数据库密码
            database='landsat_index',  # 连接数据库
        )
        mycursor = mydb.cursor()  # 创建指针

        # 生成新文件夹
        self.file_path = '{}{:0>3d}'.format(PATH, ROW)
        base_path = os.getcwd()
        self.entity_dir = os.path.join(base_path, self.file_path)
        #
        os.makedirs(self.entity_dir, exist_ok=True)
        os.chdir(self.entity_dir)

        print('Retriving {}{:0>3d}'.format(PATH, ROW))
        time_start = time.time()
        sql = "SELECT {} FROM gc_index where PRODUCT_ID != '' AND SPACECRAFT_ID = '{}' AND WRS_PATH={} AND WRS_ROW = {} AND CLOUD_COVER<={} AND DATE_ACQUIRED >='{}' AND DATE_ACQUIRED <= '{}'".format(
            INFO, SPACECRAFT, PATH, ROW, CLOUD_MAX, START_TIME, END_TIME)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        time_end = time.time()
        print('Time cost: ', time_end - time_start)
        myresult.sort()
        print("Data Num: ", len(myresult))
        # for result in myresult:
        # print(result)

        # 保存检索到的影像信息
        file_result = 'gs{}{:0>3d}_result_{}.csv'.format(PATH, ROW, SPACECRAFT)
        with open(file_result, 'w') as f:
            f.write(INFO + '\n')
            for result in myresult:
                f.write(','.join(str(i) for i in result) + '\n')
        # 保存下载链接
        self.file_url = 'gs{}{:0>3d}_url_{}.txt'.format(PATH, ROW, SPACECRAFT)
        down_url = {}
        for result in myresult:
            url_list = []
            EntityID = result[1]
            url_middle = result[4].split('//')[-1]
            url0 = '{}{}/{}_ANG.txt'.format(BASE_URL, url_middle, EntityID)
            url1 = '{}{}/{}_B1.TIF'.format(BASE_URL, url_middle, EntityID)
            url2 = '{}{}/{}_B2.TIF'.format(BASE_URL, url_middle, EntityID)
            url3 = '{}{}/{}_B3.TIF'.format(BASE_URL, url_middle, EntityID)
            url4 = '{}{}/{}_B4.TIF'.format(BASE_URL, url_middle, EntityID)
            url5 = '{}{}/{}_B5.TIF'.format(BASE_URL, url_middle, EntityID)
            url6 = '{}{}/{}_B6.TIF'.format(BASE_URL, url_middle, EntityID)
            url7 = '{}{}/{}_B7.TIF'.format(BASE_URL, url_middle, EntityID)
            url8 = '{}{}/{}_B8.TIF'.format(BASE_URL, url_middle, EntityID)
            url9 = '{}{}/{}_B9.TIF'.format(BASE_URL, url_middle, EntityID)
            url10 = '{}{}/{}_B10.TIF'.format(BASE_URL, url_middle, EntityID)
            url11 = '{}{}/{}_B11.TIF'.format(BASE_URL, url_middle, EntityID)
            url12 = '{}{}/{}_BQA.TIF'.format(BASE_URL, url_middle, EntityID)
            url13 = '{}{}/{}_MTL.txt'.format(BASE_URL, url_middle, EntityID)
            url_list = [url0, url1, url2, url3, url4, url5, url6, url7, url8, url9, url10, url11, url12, url13]
            down_url[EntityID] = url_list
        with open(self.file_url, 'w') as f:
            f.write(str(down_url))

    def _download(self, file_path):
        '''
        call IDM下载数据
        :return:
        '''
        import os
        from subprocess import call

        IDM = r'C:\Program Files (x86)\Internet Download Manager\IDMan.exe'

        # file_path = './%s/%s' % (self.file_path,self.file_url)
        print(file_path)
        base_path = os.path.dirname(os.path.abspath(str(file_path)))
        with open(file_path, 'r') as f:
            file = f.read()
        file_list = eval(file)
        for key in file_list.keys():
            entity_dir = os.path.join(base_path, key)
            os.makedirs(entity_dir, exist_ok=True)
            os.chdir(entity_dir)
            # print(os.getcwd())
            value = file_list[key]
            for url in value:
                name = url.split('/')[-1]
                print('\nDownloading: ', name)
                call([IDM, '/d', url, '/p', entity_dir, '/f', name, '/n', '/a'])
    pass



if __name__ == "__main__":
    # landsatData()._bandCombination("./datasat/")
    # landsatData()._pixExtract(['117.798147', '38.997924'], RS_dir='L:/a_遥感影像/cratchdata/122033/')
    # dataManagement().modis_pixelExtrac("/Users/Star/Desktop/python/time_series_classification/datasat/",
    #                                    "./txt/test.txt", "118.719", "36.521")
    pass
