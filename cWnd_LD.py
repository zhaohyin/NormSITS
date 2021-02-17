# -*- coding:utf-8 -*- #
'''
landsat数据常用的几个功能：
        1）landsat数据下载；
        2）数据裁剪和拼接（暂时不需要）；
        3）Landsat波段合成；
        4）直方图分析
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog
import numpy as np
import data_manager as dm
import scipy.io


class landsatDataDownUI(QDialog):
    '''
    进行landsat数据的下载
    '''
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Landsat Data Download")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        #
        # 设置按钮
        self.sql_connector = QtWidgets.QPushButton('SQL-CONNECT')
        self.lineEdit_csv = QtWidgets.QLineEdit(self)
        label1 = QtWidgets.QLabel('CLOUD-MAX')
        label2 = QtWidgets.QLabel('PATH')
        label3 = QtWidgets.QLabel('ROW')
        label4 = QtWidgets.QLabel('START-TIME')
        label5 = QtWidgets.QLabel('END-TIME')
        label6 = QtWidgets.QLabel('SPACECRAFT')
        self.lineEdit_cloud = QtWidgets.QLineEdit(self)  # CLOUD_MAX
        self.lineEdit_cloud.setText('30')
        self.lineEdit_path = QtWidgets.QLineEdit(self)   # PATH
        self.lineEdit_path.setText('122')
        self.lineEdit_row = QtWidgets.QLineEdit(self)    # ROW
        self.lineEdit_row.setText('33')
        self.lineEdit_startTime = QtWidgets.QLineEdit(self)  # START-TIME
        self.lineEdit_endTime = QtWidgets.QLineEdit(self)    # END-TIME
        self.cmobox_spaceCraft = QtWidgets.QComboBox(self) # SPACECRAFT
        self.cmobox_spaceCraft.addItems(['LANDSAT_8','LANDSAT_5','LANDSAT_7'])
        self.button_URL = QtWidgets.QPushButton('URL_ACQUIRE')
        self.button_Down = QtWidgets.QPushButton('DOWNLOAD')
        self.sql_saver = dm.landsatMysqlDown()
        #
        # 设计布局
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(self.sql_connector,0,0,1,1)
        grid.addWidget(self.lineEdit_csv,0,1,1,5)
        grid.addWidget(label1,1,0,1,1)
        grid.addWidget(self.lineEdit_cloud,1,1,1,1)
        grid.addWidget(label2,1,2,1,1)
        grid.addWidget(self.lineEdit_path,1,3,1,1)
        grid.addWidget(label3,1,4,1,1)
        grid.addWidget(self.lineEdit_row,1,5,1,1)
        grid.addWidget(label4,2,0,1,1)
        grid.addWidget(self.lineEdit_startTime,2,1,1,5)
        grid.addWidget(label5,3,0,1,1)
        grid.addWidget(self.lineEdit_endTime,3,1,1,5)
        grid.addWidget(label6,4,0,1,1)
        grid.addWidget(self.cmobox_spaceCraft,4,1,1,2)
        grid.addWidget(self.button_URL,4,3,1,2)
        grid.addWidget(self.button_Down,4,5,1,1)
        #
        # 添加槽函数
        self.sql_connector.clicked.connect(self.slot_buttonSqlConnect)
        self.button_URL.clicked.connect(self.slot_buttonURL)
        self.button_Down.clicked.connect(self.slot_buttonDownload)
        pass

    def slot_buttonSqlConnect(self):
        csvDir = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.lineEdit_csv.setText(csvDir)
        self.sql_saver._connectSQL(csvDir)

    def slot_buttonURL(self):
        cloud_max = int(self.lineEdit_cloud.text())
        path = int(self.lineEdit_path.text())
        row = int(self.lineEdit_row.text())
        startTime = self.lineEdit_startTime.text()
        endTime = self.lineEdit_endTime.text()
        spaceCraft = self.cmobox_spaceCraft.currentText()
        self.sql_saver._saveURL(cloud_max,path,row,startTime,endTime,spaceCraft)

    def slot_buttonDownload(self):
        file_path = r'%s/%s' % (self.sql_saver.entity_dir,self.sql_saver.file_url)
        self.sql_saver._download(file_path)


class landsatbandCombination(QDialog):
    '''
    目的：进行波段合成，默认为754波段合成
    输入：fileDir(影像存放路径)
    '''
    def __init__(self):
        super(landsatbandCombination, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Landsat BandCombination")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.button_rsDir = QtWidgets.QPushButton('Band_754',self)
        self.button_rsDir.setGeometry(10,10,80,20)
        self.lineEdit_rsDir = QtWidgets.QLineEdit(self)
        self.lineEdit_rsDir.setGeometry(100,10,240,20)
        self.button_excute = QtWidgets.QPushButton('EXCUTE',self)
        self.button_excute.setGeometry(260,40,80,20)
        #
        self.button_rsDir.clicked.connect(self.slot_buttonRsDir)
        self.button_excute.clicked.connect(self.slot_buttonExcute)
        pass

    def slot_buttonRsDir(self):
        rsDir = QtWidgets.QFileDialog.getExistingDirectory(self)
        dir = ("%s/" % rsDir)
        self.lineEdit_rsDir.setText(dir)

    def slot_buttonExcute(self):
        dm.landsatData()._bandCombination(self.lineEdit_rsDir.text())

class landsatDataClipUI(QDialog):
    '''
    目的：进行LANDSAT/TIFF时间序列遥感影像的裁剪
    输入：fileDir(影像存放路径)、CenterLon & CenterLat（中心像元点的经纬度）、Band（波段）、Radius（裁剪半径）
    '''
    def __init__(self):
        super().__init__()
        self.clipValues = []
        self.initUi()

    def initUi(self):
        self.setWindowTitle("Landsat/Tiff Data clip")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.button_lcDir = QtWidgets.QPushButton('LC_DIR',self)
        self.button_cenLon = QtWidgets.QPushButton('Cen_Lon',self)
        self.button_cenLat = QtWidgets.QPushButton('Cen_Lat',self)
        self.button_bandChoose = QtWidgets.QPushButton('Band',self)
        self.button_radius = QtWidgets.QPushButton('Radius',self)
        self.button_MatSaveDir = QtWidgets.QPushButton('Mat_SaveDir',self)
        self.lineEdit_lcDir = QtWidgets.QLineEdit(self)
        self.lineEdit_cenLon = QtWidgets.QLineEdit(self)
        self.lineEdit_cenLon.setText('117.361262')
        self.lineEdit_cenLat = QtWidgets.QLineEdit(self)
        self.lineEdit_cenLat.setText('39.127848')
        self.cmobox_bandChoose = QtWidgets.QComboBox(self)
        self.cmobox_bandChoose.addItems(['B1','B2','B3','B4','B5','B6','B7'])  # 主要还是使用B4波段
        self.cmobox_bandChoose.setCurrentIndex(3)
        self.lineEdit_radius = QtWidgets.QLineEdit(self)
        self.lineEdit_matSaveDir = QtWidgets.QLineEdit(self)
        self.button_clipStart = QtWidgets.QPushButton('clip',self)
        #
        #  布局
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(self.button_lcDir,0,0,1,1)
        grid.addWidget(self.lineEdit_lcDir,0,1,1,3)
        grid.addWidget(self.button_cenLon,1,0,1,1)
        grid.addWidget(self.lineEdit_cenLon,1,1,1,1)
        grid.addWidget(self.button_bandChoose,1,2,1,1)
        grid.addWidget(self.cmobox_bandChoose,1,3,1,1)
        grid.addWidget(self.button_cenLat,2,0,1,1)
        grid.addWidget(self.lineEdit_cenLat,2,1,1,1)
        grid.addWidget(self.button_radius,2,2,1,1)
        grid.addWidget(self.lineEdit_radius,2,3,1,1)
        grid.addWidget(self.button_MatSaveDir,3,0,1,1)
        grid.addWidget(self.lineEdit_matSaveDir,3,1,1,3)
        grid.addWidget(self.button_clipStart,4,3,1,1)
        #
        # 槽与信号
        self.button_lcDir.clicked.connect(self.slot_buttonLcDir)
        self.button_MatSaveDir.clicked.connect(self.slot_buttonMatSaveDir)
        self.button_clipStart.clicked.connect(self.slot_buttonClipStart)


    def slot_buttonLcDir(self):
        rsDir = QtWidgets.QFileDialog.getExistingDirectory(self)
        dir = ("%s/" % rsDir)
        self.lineEdit_lcDir.setText(dir)
        pass

    def slot_buttonMatSaveDir(self):
        matSaveDir = QtWidgets.QFileDialog.getSaveFileName(self,'Save Clip Result MatFile','./mat/','*.mat')[0]
        self.lineEdit_matSaveDir.setText((matSaveDir))
        pass

    def slot_buttonClipStart(self):
        import os
        self.clipValues = []
        for roots, dirs, files in os.walk(self.lineEdit_lcDir.text()):
            #
            # 规定读取顺序
            order_list = ['LTCP0123456789_t']
            someorder = {letter: val for val, letter in enumerate(order_list[0])}
            new_dirs = sorted(dirs, key=lambda x: [someorder.get(letter) for letter in x])
            #
            for dir in new_dirs:
                if "L" in dir:
                    tif_dir = "%s%s/" % (self.lineEdit_lcDir.text(), dir)
                    tif_name = "%s_%s.TIF" % (dir[-40:], self.cmobox_bandChoose.currentText())
                    tiff_path = os.path.join(tif_dir, tif_name)
                    #
                    clip_value = dm.landsatData()._tiffClip(tiff_path,self.lineEdit_cenLon.text(),self.lineEdit_cenLat.text(),self.lineEdit_radius.text())
                    self.clipValues.append(clip_value)
        print(np.shape(np.array(self.clipValues)))
        #
        if self.lineEdit_matSaveDir:
            scipy.io.savemat(self.lineEdit_matSaveDir.text(),{'ref_Values':self.clipValues})
        pass
    pass
