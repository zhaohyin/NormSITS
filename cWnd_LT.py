# -*- coding:utf-8 -*- #
'''
landsat时间序列数据分析子窗口：主要是进行时间序列数据的分析和处理
具体：1）landsat数据时间序列曲线获取
'''
from PyQt5 import QtCore, QtWidgets
from scipy.optimize import leastsq
import numpy as np
import data_manager as dm
import argrithms as ag
import scipy.io
import matplotlib.pyplot as plt
import matplotlib
import gdal

matplotlib.use("Qt5Agg")  # 声明使用QT5

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class landsatPIFsUI(QtWidgets.QWidget):
    '''
    目的：选则伪不变特征点--这里我选用的是基于标准差的伪不变特征点选取
    输入：*.Mat（裁剪后的数据源）
    输出：点
    '''

    def __init__(self):
        super().__init__()
        self.doys =  ['20171023', '20171108', '20171124', '20171210', '20171226', '20180111', '20180212',
                     '20180316', '20180417', '20180503', '20180519', '20180604', '20180620', '20180823',
                     '20180908', '20180924', '20181010', '20181026', '20181213', '20181229', '20190114']  # 时间点 # 获取时间点
        #
        self.initUI()
        #
        # 重要变量
        self.clipValues = []  # 裁剪区域的波段反射率
        self.clipStds = []  # 裁剪区域的标准差
        self.clipSlopes = []  # 裁剪区域的斜率
        self.pifValues = []  # PIFS的所有点的时序曲线
        self.pifDetermine = []  # PIFS判断，全是0 OR 1

    def initUI(self):
        #
        # 初始化窗口
        self.setWindowTitle('PIFs Select')
        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        #
        # 设置控件
        self.groupbox_FeatureCal = QtWidgets.QGroupBox('Feature Calculation', self)
        self.button_inputMatDir = QtWidgets.QPushButton('Input_MatDir', self)
        self.lineEdit_inputMatDir = QtWidgets.QLineEdit(self)
        self.button_stds = QtWidgets.QPushButton('stds', self)
        self.button_slopes = QtWidgets.QPushButton('slopes', self)
        #
        self.groupbox_pifsExtract = QtWidgets.QGroupBox('PIFs Extraction', self)
        self.button_pifs = QtWidgets.QPushButton('PIFs Extract', self)
        self.botton_pifsMethods = QtWidgets.QPushButton('PIFs-Methods', self)
        self.cmobox_pifsMethod = QtWidgets.QComboBox(self)
        self.button_lower = QtWidgets.QPushButton('Lower', self)
        self.button_upper = QtWidgets.QPushButton('Upper', self)
        self.lineEdit_lower = QtWidgets.QLineEdit(self)
        self.lineEdit_upper = QtWidgets.QLineEdit(self)
        self.button_export = QtWidgets.QPushButton('Export', self)
        self.button_saveMatDir = QtWidgets.QPushButton('Save_MatDir', self)
        self.lineEdit_saveMatDir = QtWidgets.QLineEdit(self)
        self.view = myView(self)
        self.scene = QtWidgets.QGraphicsScene()
        #
        self.cmobox_mode = QtWidgets.QComboBox(self)
        self.button_showImg = QtWidgets.QPushButton('Show', self)
        #
        self.groupbox_pifsOtherBands = QtWidgets.QGroupBox('PIFs-Other Bands', self)
        self.button_inputOtherBandMat = QtWidgets.QPushButton('Input-OB', self)
        self.lineEdit_inputOtherBandMat = QtWidgets.QLineEdit(self)
        self.button_pifsImport = QtWidgets.QPushButton('PIFs-Import', self)
        self.button_exportOtherBand = QtWidgets.QPushButton('Export-Values', self)
        self.lineEdit_exportOtherBand = QtWidgets.QLineEdit(self)
        # Layout
        grid = QtWidgets.QGridLayout(self)
        grid_FeatureCal = QtWidgets.QGridLayout(self.groupbox_FeatureCal)
        grid_pifsExtract = QtWidgets.QGridLayout(self.groupbox_pifsExtract)
        grid_pifsOtherBands = QtWidgets.QGridLayout(self.groupbox_pifsOtherBands)
        #
        grid.addWidget(self.groupbox_FeatureCal, 0, 0, 2, 4)
        grid.addWidget(self.groupbox_pifsExtract, 2, 0, 6, 4)
        grid.addWidget(self.view, 0, 4, 10, 8)
        grid.addWidget(self.groupbox_pifsOtherBands, 8, 0, 2, 4)
        self.view.setFixedWidth(500)
        #
        grid_FeatureCal.addWidget(self.button_inputMatDir, 0, 0, 1, 1)
        grid_FeatureCal.addWidget(self.lineEdit_inputMatDir, 0, 1, 1, 3)
        grid_FeatureCal.addWidget(self.button_stds, 1, 2, 1, 1)
        grid_FeatureCal.addWidget(self.button_slopes, 1, 3, 1, 1)
        #
        grid_pifsExtract.addWidget(self.botton_pifsMethods, 0, 0, 1, 1)
        grid_pifsExtract.addWidget(self.cmobox_pifsMethod, 0, 1, 1, 3)
        grid_pifsExtract.addWidget(self.button_lower, 1, 0, 1, 1)
        grid_pifsExtract.addWidget(self.lineEdit_lower, 1, 1, 1, 3)
        grid_pifsExtract.addWidget(self.button_upper, 2, 0, 1, 1)
        grid_pifsExtract.addWidget(self.lineEdit_upper, 2, 1, 1, 3)
        grid_pifsExtract.addWidget(self.button_pifs, 3, 2, 1, 2)
        grid_pifsExtract.addWidget(self.button_saveMatDir, 4, 0, 1, 1)
        grid_pifsExtract.addWidget(self.lineEdit_saveMatDir, 4, 1, 1, 3)
        grid_pifsExtract.addWidget(self.cmobox_mode, 5, 0, 1, 1)
        grid_pifsExtract.addWidget(self.button_showImg, 5, 1, 1, 1)
        grid_pifsExtract.addWidget(self.button_export, 5, 2, 1, 2)
        #
        grid_pifsOtherBands.addWidget(self.button_inputOtherBandMat, 0, 0, 1, 1)
        grid_pifsOtherBands.addWidget(self.lineEdit_inputOtherBandMat, 0, 1, 1, 3)
        grid_pifsOtherBands.addWidget(self.button_pifsImport, 1, 0, 1, 1)
        grid_pifsOtherBands.addWidget(self.button_exportOtherBand, 1, 1, 1, 1)
        grid_pifsOtherBands.addWidget(self.lineEdit_exportOtherBand, 1, 2, 1, 2)
        #
        # 初始化
        self.cmobox_pifsMethod.addItems(['std', 'slope'])
        self.cmobox_mode.addItems(['img-stds', 'img-pifsDerterMined', 'img-slopes'])
        self.botton_pifsMethods.setDisabled(True)
        self.button_lower.setDisabled(True)
        self.button_upper.setDisabled(True)
        self.button_pifs.setDisabled(True)
        self.button_exportOtherBand.setDisabled(True)
        self.button_pifs.setStyleSheet("background-color: blue")
        self.button_export.setStyleSheet("background-color: blue")
        self.button_pifsImport.setStyleSheet("background-color: blue")
        # 槽和函数
        self.button_inputMatDir.clicked.connect(self.slot_buttonInputMatDir)  # 输入Mat路径
        self.button_slopes.clicked.connect(self.slot_buttonSlope)  # 对比PIF选择方法
        self.button_stds.clicked.connect(self.slot_buttonStd)  # 计算研究区域的标准差
        self.button_pifs.clicked.connect(self.slot_buttonPifs)  # 计算研究区域的PIFs,0 OR 1
        self.button_showImg.clicked.connect(self.slot_buttonShowImg)  # 显示图像
        self.button_export.clicked.connect(self.slot_buttonExport)  # 输出图像代表的数据
        self.button_saveMatDir.clicked.connect(self.slot_buttonSaveMatDir)  # 输入保存mat路径
        #
        self.button_inputOtherBandMat.clicked.connect(self.slot_buttonInputOtherBandMat)  # 输入其他波段的反射率数据
        self.button_pifsImport.clicked.connect(self.slot_buttonPIFsImport)  # PIFs提取
        self.button_exportOtherBand.clicked.connect(self.slot_buttonExportOtherBandsValues)  # PIFs提取波段数据

    def slot_buttonInputMatDir(self):
        #
        # 添加路径
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.lineEdit_inputMatDir.setText(open_filename)
        if 'S1000' in self.lineEdit_inputMatDir.text():
            self.clipValues = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['ref_Values']  # eg[21,1001,1001]
            print(np.shape(np.array(self.clipValues)))
            self.button_pifs.setDisabled(False)

    def slot_buttonSlope(self):
        #
        self.cmobox_mode.setCurrentIndex(2)
        self.cmobox_pifsMethod.setCurrentIndex(1)
        if 'slope' in self.lineEdit_inputMatDir.text():
            self.clipSlopes = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['slopes']
        else:
            self.clipValues = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['ref_Values']  # eg[21,1001,1001]
            print(np.shape(np.array(self.clipValues)))
            #
            # 排序后最小二乘法估算斜率
            arrays_clip = np.array(self.clipValues).astype(float)
            for i in range(np.shape(arrays_clip)[1]):
                col = []
                for j in range(np.shape(arrays_clip)[2]):
                    #
                    Yi = np.sort(arrays_clip[:, i, j])
                    Xi = range(len(Yi))
                    p0 = [1, 20]
                    Para = leastsq(self.error, p0, args=(Xi, Yi))
                    slope, _ = Para[0]  # 最小二乘法对排序累加后的DN值进行计算
                    col.append(slope)
                self.clipSlopes.append(col)
            #
        print(np.shape(np.array(self.clipSlopes)))  # [1001,1001]
        print(np.percentile(self.clipSlopes, 1), np.percentile(self.clipSlopes, 99))
        pass

    def func(self, p, x):  ##需要拟合的函数func :指定函数的形状
        k, b = p
        return k * x + b

    def error(self, p, x, y):  ##偏差函数：x,y都是列表:这里的x,y更上面的Xi,Yi中是一一对应的
        return self.func(p, x) - y

    def slot_buttonStd(self):
        #
        # 初始化
        self.clipStds = []
        self.cmobox_mode.setCurrentIndex(0)
        self.cmobox_pifsMethod.setCurrentIndex(0)
        #
        # 输入数据
        if 'std' in self.lineEdit_inputMatDir.text():
            self.clipStds = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['stds']
        else:
            self.clipValues = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['ref_Values']  # eg[21,1001,1001]
            print(np.shape(np.array(self.clipValues)))
            #
            # 计算DN值的方差，[0,1] * 255 -> [0,255]
            arrays_clip = np.array(self.clipValues).astype(float)
            for i in range(np.shape(arrays_clip)[1]):
                col = []
                for j in range(np.shape(arrays_clip)[2]):
                    std = np.round(np.std(255 * arrays_clip[:, i, j]), 5)
                    col.append(std)
                self.clipStds.append(col)
        #
        print(np.shape(np.array(self.clipStds)))  # [1001,1001]
        print(np.percentile(self.clipStds, 1), np.percentile(self.clipStds, 99))

    def slot_buttonPifs(self):
        '''
        目的：获取PIFS的特征矩阵和时序曲线值
        '''
        #
        self.pifValues = []
        self.pifDetermine = []
        self.cmobox_mode.setCurrentIndex(1)
        flag = 0
        #
        if 'PIF' in self.lineEdit_inputMatDir.text():
            self.pifValues = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['PIFs_Refvalues']
            self.pifDetermine = scipy.io.loadmat(self.lineEdit_inputMatDir.text())['PIFs_determine']
        #
        else:
            #
            arrays_values = np.array(self.clipValues).astype(float)
            #
            # 根据方差来进行计算
            if self.cmobox_pifsMethod.currentIndex() == 0:
                #
                # 设定阈值
                lower_limit = float(self.lineEdit_lower.text())
                upper_limit = float(self.lineEdit_upper.text())
                #
                arrays_stds = np.array(self.clipStds).astype(float)
                for i in range(np.shape(arrays_stds)[0]):
                    col1 = []
                    for j in range(np.shape(arrays_stds)[1]):
                        # 判定
                        if arrays_stds[i, j] < upper_limit and arrays_stds[i, j] > lower_limit and arrays_values[
                            12, i, j] > 0.1 and np.max(arrays_values[:, i, j]) < 0.4:
                            flag = 1
                            row = []
                            row.extend(arrays_values[:, i, j])
                            row.extend([(i + 2572), (j + 2108)])
                            self.pifValues.append(row)
                        else:
                            flag = 0
                        #
                        col1.append(flag)
                    self.pifDetermine.append(col1)
            #
            # 根据论文'A Long Time-Series Radiometric Normalization Method for Landsat Images'里提出的方法
            if self.cmobox_pifsMethod.currentIndex() == 1:
                #
                # 设定阈值
                lower_limit = float(self.lineEdit_lower.text())
                upper_limit = float(self.lineEdit_upper.text())
                #
                arrays_slopes = np.array(self.clipSlopes).astype(float)
                for i in range(np.shape(arrays_slopes)[0]):
                    col1 = []
                    for j in range(np.shape(arrays_slopes)[1]):
                        #
                        if arrays_slopes[i, j] <= upper_limit and arrays_slopes[i, j] >= lower_limit and arrays_values[
                            12, i, j] > 0.1 and np.max(arrays_values[:, i, j]) < 0.4:
                            flag = 1
                            row = []
                            row.extend(arrays_values[:, i, j])
                            row.extend([(i + 2572), (j + 2108)])
                            self.pifValues.append(row)
                        else:
                            flag = 0
                        col1.append(flag)
                    self.pifDetermine.append(col1)
        #
        print(np.shape(self.pifValues))
        pass

    def slot_buttonShowImg(self):
        '''
        目的：结果可视化
        '''
        self.scene = QtWidgets.QGraphicsScene()
        #
        if self.cmobox_mode.currentIndex() == 0:
            self.img = myFigure(width=3, height=3)
            pos = plt.imshow(self.clipStds, cmap='jet')
            plt.xticks(fontsize=3)
            plt.yticks(fontsize=3)
            cb = plt.colorbar(pos, shrink=0.8)
            cb.ax.tick_params(labelsize=3)
            self.scene.addWidget(self.img)
            self.view.setScene(self.scene)
        #
        if self.cmobox_mode.currentIndex() == 1:
            self.img = myFigure(width=3, height=3)
            pos = plt.imshow(self.pifDetermine, cmap='binary')
            plt.xticks(fontsize=3)
            plt.yticks(fontsize=3)
            cb = plt.colorbar(pos, shrink=0.8)
            cb.ax.tick_params(labelsize=3)
            self.scene.addWidget(self.img)
            self.view.setScene(self.scene)
        #
        if self.cmobox_mode.currentIndex() == 2:
            self.img = myFigure(width=3, height=3)
            pos = plt.imshow(self.clipSlopes, cmap='jet')
            plt.xticks(fontsize=3)
            plt.yticks(fontsize=3)
            cb = plt.colorbar(pos, shrink=0.8)
            cb.ax.tick_params(labelsize=3)
            self.scene.addWidget(self.img)
            self.view.setScene(self.scene)

    def slot_buttonExport(self):
        '''
        目的：输出结果
        '''
        if self.lineEdit_saveMatDir.text():
            if self.cmobox_mode.currentIndex() == 0:
                scipy.io.savemat(self.lineEdit_saveMatDir.text(), {'stds': self.clipStds})
            if self.cmobox_mode.currentIndex() == 1:
                scipy.io.savemat(self.lineEdit_saveMatDir.text(),
                                 {'PIFs_determine': self.pifDetermine, 'PIFs_Refvalues': self.pifValues})
            if self.cmobox_mode.currentIndex() == 2:
                scipy.io.savemat(self.lineEdit_saveMatDir.text(), {'slopes': self.clipSlopes})
        pass

    def slot_buttonSaveMatDir(self):
        '''
        目的：输入储存的路径
        '''
        matSaveDir = QtWidgets.QFileDialog.getSaveFileName(self, 'Save PIFs MatFile', './mat/', '*.mat')[0]
        self.lineEdit_saveMatDir.setText(matSaveDir)
        pass

    def slot_buttonInputOtherBandMat(self):
        '''
        获取其他波段的PIFs数据
        '''
        #
        # 添加路径
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.lineEdit_inputOtherBandMat.setText(open_filename)
        if 'S1000' in self.lineEdit_inputOtherBandMat.text():
            self.clipValues = scipy.io.loadmat(self.lineEdit_inputOtherBandMat.text())['ref_Values']  # eg[21,1001,1001]
            print(np.shape(np.array(self.clipValues)))
            self.button_exportOtherBand.setDisabled(False)
        pass

    def slot_buttonPIFsImport(self):
        #
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.pifDetermine = scipy.io.loadmat(open_filename)['PIFs_determine']
        #
        print(np.shape(np.array(self.pifDetermine)))

    def slot_buttonExportOtherBandsValues(self):
        #
        pifSaveDir = QtWidgets.QFileDialog.getSaveFileName(self, 'OtherBands-PIFs', './mat/', '*.mat')[0]
        self.lineEdit_exportOtherBand.setText(str(pifSaveDir))
        #
        shape = np.shape(np.array(self.pifDetermine))
        array_pifDetermine = np.array(self.pifDetermine)
        array_clipValues = np.array(self.clipValues)  # np.array尽量放在循环外面，防止每次循环都要调用内存
        pifSamples = []
        for i in range(shape[0]):
            for j in range(shape[1]):
                if array_pifDetermine[i, j] == 1:
                    pifSamples.append(array_clipValues[:, i, j])
        #
        self.pifValues = pifSamples
        print(np.shape(np.array(self.pifValues)))
        #
        scipy.io.savemat(pifSaveDir, {'PIFs_determine': self.pifDetermine, 'PIFs_Refvalues': self.pifValues})
        pass


class landsatTSRRNormalizationUI(QtWidgets.QWidget):
    '''
    目的：进行时序遥感影像的相对校正
    输入：1）时序反射率MAT数据；2）PIFS点的MAT数据
    '''
    def __init__(self):
        super().__init__()
        self.doys = ['20171023', '20171108', '20171124', '20171210', '20171226', '20180111', '20180212',
                     '20180316', '20180417', '20180503', '20180519', '20180604', '20180620', '20180823',
                     '20180908', '20180924', '20181010', '20181026', '20181213', '20181229', '20190114']   # 获取时间点
        #
        self.rData = []  # 仅仅是为了作图！！！
        self.gData = []
        self.bData = []
        #
        # Bp预测值
        self.clipValues = []  # 输入的裁剪区的值
        #
        # Bp训练值
        self.pifsValues = []  # 输入文件中PIFs的值[训练值]
        self.pifsCorrValues = []  # PIFs校正后的值
        #
        # Bp测试值
        self.pifsTestValues = []  # 输入测试的PIFs值
        self.pifsTestCorrValues = []  # 模型运行后的PIFs结果
        #
        self.correctedValues = []  # 校正后的数据
        self.keys = []  # 模型的参数
        #
        self.pifStds = []  # 原始数据的标准差
        self.sortMap = []  # 升序排序映射
        self.corrOrder = []  # 满足最小期望的映射关系
        #
        # BP 神经网络的必要参数
        self.ih_w = []
        self.ho_w = []
        self.hide_b0 = []
        self.out_b0 = []
        #
        self.initUi()
        self.layoutUI()
        self.single_slot()

    def initUi(self):
        #
        self.setWindowTitle('NMAG METHOD')
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        #
        # 设置组件
        self.groupbox_inputMat = QtWidgets.QGroupBox('Input-Mat', self)
        self.groupbox_MethodChoose = QtWidgets.QGroupBox('RRN Method Choose', self)
        self.groupbox_Train = QtWidgets.QGroupBox('Train', self)
        self.groupbox_Test = QtWidgets.QGroupBox('Test', self)
        self.groupbox_Pred = QtWidgets.QGroupBox('Pred-ClipValues', self)
        # 设置控件
        self.button_inputRefMatDir = QtWidgets.QPushButton('Input_ClipValues', self)
        self.button_inputPIFsMatDir = QtWidgets.QPushButton('Input_PIFsDir', self)
        self.lineEdit_inputRefMatDir = QtWidgets.QLineEdit(self)
        self.lineEdit_inputPIFsMatDir = QtWidgets.QLineEdit(self)
        self.button_pccs = QtWidgets.QPushButton('pcc')
        #
        # rrnChoose
        self.button_rrnMethod = QtWidgets.QPushButton('Methods', self)
        self.cmobox_rrnMethod = QtWidgets.QComboBox(self)
        self.button_initValue = QtWidgets.QPushButton('InitValue', self)
        self.cmobox_initValue = QtWidgets.QComboBox(self)
        self.button_outydValue = QtWidgets.QPushButton('out_yd', self)
        self.cmobox_outydValue = QtWidgets.QComboBox(self)
        # BP-train
        self.button_trainSample = QtWidgets.QPushButton('TrainSam', self)
        self.lineEdit_trainSample = QtWidgets.QLineEdit(self)
        self.table_trainModelKey = QtWidgets.QTableWidget(self)
        self.view = myView(self)
        self.button_keySave = QtWidgets.QPushButton('KeySave', self)
        self.button_trainBP = QtWidgets.QPushButton('Train-BP', self)
        self.lineEdit_corrOrder = QtWidgets.QLineEdit(self)
        self.lineEdit_imgProcess = QtWidgets.QLineEdit(self)
        self.button_imgProcessMap = QtWidgets.QPushButton('拟合过程', self)
        self.lineEdit_KeySaveDir = QtWidgets.QLineEdit(self)
        # BP-test
        self.button_contrastMethod = QtWidgets.QPushButton('Method', self)
        self.cmobox_contrastMethod = QtWidgets.QComboBox(self)
        self.button_testSample = QtWidgets.QPushButton('TestSam', self)
        self.lineEdit_testSample = QtWidgets.QLineEdit(self)
        self.button_testImportKeys = QtWidgets.QPushButton('Import Keys', self)
        self.button_testBp = QtWidgets.QPushButton('Test-Bp', self)
        self.button_rmseCal = QtWidgets.QPushButton('RMSE', self)
        self.lineEdit_rmseCal = QtWidgets.QLineEdit(self)
        # BP-Pred
        self.button_predSample = QtWidgets.QPushButton('PredSam', self)
        self.lineEdit_predSample = QtWidgets.QLineEdit(self)
        self.button_importKeys = QtWidgets.QPushButton('Import Keys', self)
        self.button_predBP = QtWidgets.QPushButton('Pred-NMAG', self)
        self.button_bpMatSaveDir = QtWidgets.QPushButton('NMAG-SaveDir', self)
        self.lineEdit_bpMatSaveDir = QtWidgets.QLineEdit(self)
        self.button_startBP = QtWidgets.QPushButton('Save-NMAG', self)
        # 植被指数补充结果
        self.button_viSaveDir = QtWidgets.QPushButton('VI-SaveDir', self)
        self.lineEdit_viSaveDir = QtWidgets.QLineEdit(self)
        self.button_viCal = QtWidgets.QPushButton('VI-Cal', self)
        # RGB 可视化结果
        self.groupbox_mat2rgb = QtWidgets.QGroupBox('mat-RGB-Combination', self)
        self.button_rMatInput = QtWidgets.QPushButton('R-Mat', self)
        self.button_gMatInput = QtWidgets.QPushButton('G-Mat', self)
        self.button_bMatInput = QtWidgets.QPushButton('B-Mat', self)
        self.lineEdit_rMatDir = QtWidgets.QLineEdit(self)
        self.lineEdit_gMatDir = QtWidgets.QLineEdit(self)
        self.lineEdit_bMatDir = QtWidgets.QLineEdit(self)
        self.button_matMode = QtWidgets.QPushButton('mat-Mode', self)  # 合成看是校正前还是校正后
        self.cmobox_matMode = QtWidgets.QComboBox(self)
        self.button_rgbSaveDir = QtWidgets.QPushButton('RGB-SaveDir', self)
        self.lineEdit_rgbSaveDir = QtWidgets.QLineEdit(self)
        self.button_startConvert = QtWidgets.QPushButton('Start-Convert', self)

        # 初始化
        self.lineEdit_inputRefMatDir.setText('./mat/B5测试样/B5S1000.mat')
        self.lineEdit_inputPIFsMatDir.setText('./mat/B5测试样/PIFs-slopes-改.mat')
        self.cmobox_rrnMethod.addItems(['NMAG'])
        self.cmobox_initValue.addItems(['init', 'maxStds', 'maxMeans'])
        self.cmobox_outydValue.addItems(['mean', 'minSSE'])
        #
        self.cmobox_contrastMethod.addItems(['NMAG'])
        self.lineEdit_trainSample.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_testSample.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_predSample.setAlignment(QtCore.Qt.AlignCenter)
        self.cmobox_matMode.addItems(['校正前(ref_Values)', '校正后(BP_CorrValues)'])
        #
        self.table_trainModelKey.setRowCount(4)
        self.table_trainModelKey.setColumnCount(1)
        self.table_trainModelKey.setHorizontalHeaderLabels(['Key'])
        self.table_trainModelKey.setVerticalHeaderLabels(['BpInNode', 'HideLyNum', 'BpHideNode', 'BpOutNode'])
        self.table_trainModelKey.setItem(0, 0, QtWidgets.QTableWidgetItem(str('1')))
        self.table_trainModelKey.setItem(1, 0, QtWidgets.QTableWidgetItem(str('1')))
        self.table_trainModelKey.setItem(2, 0, QtWidgets.QTableWidgetItem(str('10')))
        self.table_trainModelKey.setItem(3, 0, QtWidgets.QTableWidgetItem(str('1')))
        self.table_trainModelKey.setDisabled(True)
        #
        self.button_initValue.setDisabled(True)
        self.cmobox_initValue.setDisabled(True)
        self.button_outydValue.setDisabled(True)
        self.cmobox_outydValue.setDisabled(True)
        #
        self.button_trainBP.setDisabled(True)
        self.button_keySave.setDisabled(True)
        self.button_imgProcessMap.setDisabled(True)
        self.button_testBp.setDisabled(True)
        self.button_predBP.setDisabled(True)
        self.button_matMode.setDisabled(True)
        self.button_startConvert.setDisabled(True)
        self.button_viCal.setDisabled(True)
        #
        self.button_trainBP.setStyleSheet("background-color: blue")
        self.button_testBp.setStyleSheet("background-color: blue")
        self.button_predBP.setStyleSheet("background-color: blue")
        self.button_startConvert.setStyleSheet("background-color: blue")
        self.button_viCal.setStyleSheet("background-color: blue")

    def layoutUI(self):
        #
        grid = QtWidgets.QGridLayout(self)
        grid.addWidget(self.groupbox_inputMat, 0, 0, 2, 4)
        grid.addWidget(self.groupbox_MethodChoose, 2, 0, 2, 4)
        grid.addWidget(self.groupbox_Train, 4, 0, 5, 4)
        grid.addWidget(self.groupbox_Test, 9, 0, 5, 4)
        grid.addWidget(self.groupbox_Pred, 14, 0, 4, 4)
        grid.addWidget(self.groupbox_mat2rgb, 0, 6, 6, 4)
        grid.addWidget(self.view, 6, 6, 12 ,4)
        self.view.setFixedWidth(500)
        self.view.setFixedHeight(400)
        self.groupbox_Test.setFixedWidth(500)
        #
        grid_inputMat = QtWidgets.QGridLayout(self.groupbox_inputMat)
        grid_rrnChoose = QtWidgets.QGridLayout(self.groupbox_MethodChoose)
        grid_train = QtWidgets.QGridLayout(self.groupbox_Train)
        grid_test = QtWidgets.QGridLayout(self.groupbox_Test)
        grid_pred = QtWidgets.QGridLayout(self.groupbox_Pred)
        grid_mat2rgb = QtWidgets.QGridLayout(self.groupbox_mat2rgb)
        #
        grid_inputMat.addWidget(self.button_inputRefMatDir, 0, 0, 1, 1)  # 输入文本框模式
        grid_inputMat.addWidget(self.lineEdit_inputRefMatDir, 0, 1, 1, 5)
        grid_inputMat.addWidget(self.button_inputPIFsMatDir, 1, 0, 1, 1)
        grid_inputMat.addWidget(self.lineEdit_inputPIFsMatDir, 1, 1, 1, 5)
        #
        grid_rrnChoose.addWidget(self.button_rrnMethod, 0, 0, 1, 1)  # 方法选择模块
        grid_rrnChoose.addWidget(self.cmobox_rrnMethod, 0, 1, 1, 3)
        grid_rrnChoose.addWidget(self.button_initValue, 1, 0, 1, 1)
        grid_rrnChoose.addWidget(self.cmobox_initValue, 1, 1, 1, 1)
        grid_rrnChoose.addWidget(self.button_outydValue, 1, 2, 1, 1)
        grid_rrnChoose.addWidget(self.cmobox_outydValue, 1, 3, 1, 1)
        #
        grid_train.addWidget(self.button_trainSample, 0, 0, 1, 1)  # BP训练模块
        grid_train.addWidget(self.lineEdit_trainSample, 0, 1, 1, 1)
        grid_train.addWidget(self.button_trainBP, 1, 0, 1, 1)
        grid_train.addWidget(self.button_keySave, 1, 1, 1, 1)
        grid_train.addWidget(self.lineEdit_KeySaveDir, 2, 0, 1, 2)
        grid_train.addWidget(self.button_imgProcessMap, 3, 0, 1, 1)
        grid_train.addWidget(self.lineEdit_imgProcess, 3, 1, 1, 1)
        grid_train.addWidget(self.lineEdit_corrOrder, 4, 0, 1, 4)
        grid_train.addWidget(self.table_trainModelKey, 0, 2, 4, 2)
        #
        grid_pred.addWidget(self.button_predSample, 0, 0, 1, 1)  # BP预测模块
        grid_pred.addWidget(self.lineEdit_predSample, 0, 1, 1, 1)
        grid_pred.addWidget(self.button_importKeys, 0, 2, 1, 1)
        grid_pred.addWidget(self.button_predBP, 0, 3, 1, 1)
        grid_pred.addWidget(self.button_bpMatSaveDir, 1, 0, 1, 1)
        grid_pred.addWidget(self.lineEdit_bpMatSaveDir, 1, 1, 1, 3)
        grid_pred.addWidget(self.button_startBP, 2, 3, 1, 1)
        #
        grid_test.addWidget(self.button_contrastMethod, 0, 0, 1, 1)  # BP测试模块
        grid_test.addWidget(self.cmobox_contrastMethod, 0, 1, 1, 3)
        grid_test.addWidget(self.button_testSample, 1, 0, 1, 1)
        grid_test.addWidget(self.lineEdit_testSample, 1, 1, 1, 1)
        grid_test.addWidget(self.button_testImportKeys, 1, 2, 1, 1)
        grid_test.addWidget(self.button_testBp, 1, 3, 1, 1)
        grid_test.addWidget(self.button_rmseCal, 2, 0, 1, 1)
        grid_test.addWidget(self.lineEdit_rmseCal, 2, 1, 1, 3)
        #
        grid_mat2rgb.addWidget(self.button_matMode, 0, 0, 1, 1)
        grid_mat2rgb.addWidget(self.cmobox_matMode, 0, 1, 1, 1)
        grid_mat2rgb.addWidget(self.button_rMatInput, 1, 0, 1, 1)
        grid_mat2rgb.addWidget(self.button_gMatInput, 2, 0, 1, 1)
        grid_mat2rgb.addWidget(self.button_bMatInput, 3, 0, 1, 1)
        grid_mat2rgb.addWidget(self.lineEdit_rMatDir, 1, 1, 1, 3)
        grid_mat2rgb.addWidget(self.lineEdit_gMatDir, 2, 1, 1, 3)
        grid_mat2rgb.addWidget(self.lineEdit_bMatDir, 3, 1, 1, 3)
        grid_mat2rgb.addWidget(self.button_rgbSaveDir, 4, 0, 1, 1)
        grid_mat2rgb.addWidget(self.lineEdit_rgbSaveDir, 4, 1, 1, 2)
        grid_mat2rgb.addWidget(self.button_startConvert, 4, 3, 1, 1)
        grid_mat2rgb.addWidget(self.button_viSaveDir, 5, 0, 1, 1)
        grid_mat2rgb.addWidget(self.lineEdit_viSaveDir, 5, 1, 1, 2)
        grid_mat2rgb.addWidget(self.button_viCal, 5, 3, 1, 1)
        pass

    def single_slot(self):
        self.button_inputRefMatDir.clicked.connect(self.slot_buttonInputRefDir)
        self.button_inputPIFsMatDir.clicked.connect(self.slot_buttonInputPIFsDir)
        #
        self.button_trainSample.clicked.connect(self.slot_buttonTrainSample)  # 输入训练样本
        self.button_trainBP.clicked.connect(self.slot_buttonTrainBp)  # 模型训练
        self.button_keySave.clicked.connect(self.slot_buttonKeySave)  # 保存权重和阈值
        self.button_imgProcessMap.clicked.connect(self.slot_buttonImgProcessMap)  # 对拟合过程进行监测
        #
        self.button_testSample.clicked.connect(self.slot_buttonTestSample)  # 输入测试样本
        self.button_testImportKeys.clicked.connect(self.slot_buttonImportKeys)  # 输入参数Bp
        self.button_testBp.clicked.connect(self.slot_buttonTestBp)  # 进行测试BP样本集的输出
        self.button_rmseCal.clicked.connect(self.slot_buttonRMSECal)  # RMSE计算
        #
        self.button_predSample.clicked.connect(self.slot_buttonPredSample)  # 输入预测样本
        self.button_importKeys.clicked.connect(self.slot_buttonImportKeys)  # 输入参数【同test】
        self.button_predBP.clicked.connect(self.slot_buttonPredBp)  # 进行预测BP样本集的输出
        self.button_startBP.clicked.connect(self.slot_buttonBpStartDir)  # 保存结果
        self.button_bpMatSaveDir.clicked.connect(self.slot_buttonBpMatSaveDir)
        #
        self.button_viSaveDir.clicked.connect(self.slot_buttonVIsaveDir)  # 输入保存NDVI的路径
        self.button_viCal.clicked.connect(self.slot_buttonVICal)  # 保存NDVI的数值
        #
        self.button_rMatInput.clicked.connect(self.slot_buttonRMatInput)  # 输入各个波段的Mat数据
        self.button_gMatInput.clicked.connect(self.slot_buttonGMatInput)
        self.button_bMatInput.clicked.connect(self.slot_buttonBMatInput)
        self.button_rgbSaveDir.clicked.connect(self.slot_buttonRgbSaveDir)  # 输入保存RGB的路径
        self.button_startConvert.clicked.connect(self.slot_buttonStartConvert)  # 开始进行转换

        pass

    def slot_buttonInputRefDir(self):
        #
        # 输入裁剪后的时间序列反射率数据
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.lineEdit_inputRefMatDir.setText(open_filename)
        pass

    def slot_buttonInputPIFsDir(self):
        #
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.lineEdit_inputPIFsMatDir.setText(open_filename)

    def slot_buttonLsmCorredSaveDir(self):
        #
        corredSaveDir = QtWidgets.QFileDialog.getSaveFileName(self, '校正后波段反射率数据', './mat/', '*.mat')[0]
        self.lineEdit_lsmCorredSaveDir.setText(corredSaveDir)


    '''
    NMAG 槽函数
    '''
    def slot_buttonTrainSample(self):
        self.pifsValues = scipy.io.loadmat(self.lineEdit_inputPIFsMatDir.text())['PIFs_Refvalues']  # [num,23]
        print(np.shape(np.array(self.pifsValues)))
        self.lineEdit_trainSample.setText(str(np.shape(np.array(self.pifsValues))[0]))
        self.button_trainBP.setDisabled(False)
        self.button_keySave.setDisabled(False)
        self.table_trainModelKey.setDisabled(False)


    def slot_buttonTrainBp(self):
        #
        # 变量初始化
        bpInNode = int(self.table_trainModelKey.item(0, 0).text())
        bpHideNode = int(self.table_trainModelKey.item(2, 0).text())
        bpOutNode = int(self.table_trainModelKey.item(3, 0).text())
        #
        self.ih_w = []
        self.ho_w = []
        self.hide_b0 = []
        self.out_b0 = []
        #
        # BP简单
        # self.lossFig = myFigure()
        # BP + 贪婪算法 (NMAG)
        if self.cmobox_rrnMethod.currentIndex() == 0:
            #
            # 初始化
            m_Outsample = []
            self.corrOrder = []  # 映射
            self.pifsCorrValues = []
            #
            array_ih_w = np.zeros([len(self.doys), bpInNode, bpHideNode])
            array_ho_w = np.zeros([len(self.doys), bpHideNode, bpOutNode])
            array_hide_b0 = np.zeros([len(self.doys), bpHideNode])
            array_out_b0 = np.zeros([len(self.doys), bpOutNode])
            #
            # 选定初始影像
            # 1.添加初始时间20171023
            self.corrOrder.append(0)
            #
            m_Outsample.append(np.array(self.pifsValues)[:, self.corrOrder[0]])  # 起始参考值
            #
            print('First Map is : %s' % self.doys[int(self.corrOrder[0])])
            print(np.array(m_Outsample)[0, :])
            #
            for i in range(1, len(self.doys)):
                #
                # 获取最小期望值的index
                rmse_sum = np.zeros([len(self.doys)])
                array_Outsample = np.array(m_Outsample)  # 预测值集合的数组
                for j in range(len(self.doys)):
                    if j in self.corrOrder:
                        rmse_sum[j] = 99999
                    else:
                        #
                        sum = 0.0
                        for p in range(np.shape(array_Outsample)[0]):
                            z0 = np.array(self.pifsValues)[:, j] - array_Outsample[p, :]  # xi - f(xj)
                            sum += np.sum(z0 * z0)  # sum((xi-f(xj))*(xi-(f(xj)))
                        rmse_sum[j] = sum
                #
                index = np.argsort(rmse_sum)[0]
                print('\nNow input %s data' % self.doys[index])
                self.corrOrder.append(index)
                #
                # 输入层
                m_Insample = np.array(self.pifsValues)[:, index]  # 待校正-输入值
                print('Insam:', m_Insample)
                #
                train_bp = ag.bpNet(bpInNode, bpHideNode, bpOutNode, imgNum=i, Greedy=True)   ## 直接构造损失函数，进行梯度下降
                train_bp.bpInitNetFunc()
                #
                times = 0
                err = []
                err_time = []
                while train_bp.totalErr > 0.0001 and times < 1000:
                    times += 1
                    train_bp.bpNetTrainFunc(m_Insample, m_Outsample, imgNum=i, Greedy=True)
                    if (times + 1) % 10 == 0:
                        print('Doys %s BP %5d DT:%10.5f\n' % (self.doys[index], (times + 1), train_bp.totalErr))
                        err.append(train_bp.totalErr)
                        err_time.append(times + 1)
                #
                # 绘制损失函数曲线
                plt.plot(err_time, err)
                #
                # 储存误差矩阵
                scipy.io.savemat(f'./mat/{self.doys[index]}_HideNode_{bpHideNode}.mat',{'err_time':err_time,'error':err})
                #
                # 加入计算结果
                #
                corrValue = []
                for h in range(np.shape(np.array(m_Insample))[0]):
                    train_bp.bpNetRecognizeFunc(m_Insample[h])
                    corrValue.extend(train_bp.out_y0.tolist())
                #
                print('out_y0:', np.array(corrValue))
                m_Outsample.append(corrValue)  # 添加预测值作为参考值，保证局部最优
                #
                array_ih_w[index, :, :] = train_bp.ih_w  # 期望结果：[21,1,10]
                array_ho_w[index, :, :] = train_bp.ho_w  # [21,10,1]
                array_hide_b0[index, :] = train_bp.hide_b0  # [21,10]
                array_out_b0[index, :] = train_bp.out_b0  # [21,1]
            #
            # 保存变量
            self.ih_w = array_ih_w.tolist()
            self.ho_w = array_ho_w.tolist()
            self.hide_b0 = array_hide_b0.tolist()
            self.out_b0 = array_out_b0.tolist()
            self.pifsCorrValues = m_Outsample
            print(np.shape(np.array(m_Outsample)))
            print(self.corrOrder)
            pass

        #
        # 显示图像
        xlabel = [10, 50, 100, 300, 500, 1000]
        plt.xticks(xlabel, fontsize=5,rotation=45)
        ylabel = [0, 1, 2, 3,4,5]
        plt.yticks(ylabel, fontsize=5)
        self.lossFig.ax.set_title('loss')
        self.scence = QtWidgets.QGraphicsScene()
        self.scence.addWidget(self.lossFig)
        self.view.setScene(self.scence)


    def slot_buttonKeySave(self):
        #
        # 保存模型参数
        #
        saveDir = QtWidgets.QFileDialog.getSaveFileName(self, 'BPNet', './mat/', '*.mat')[0]
        self.lineEdit_KeySaveDir.setText(saveDir)
        #
        if saveDir:
            if self.cmobox_rrnMethod.currentIndex() == 1:  # 针对两景遥感影像而言
                scipy.io.savemat(saveDir,
                                 {'ih_w': self.ih_w, 'ho_w': self.ho_w,
                                  'hide_b0': self.hide_b0, 'out_b0': self.out_b0})
            if self.cmobox_rrnMethod.currentIndex() == 3 or self.cmobox_rrnMethod.currentIndex() == 4 or self.cmobox_rrnMethod.currentIndex() == 5:
                scipy.io.savemat(saveDir,
                                 {'ih_w': self.ih_w, 'ho_w': self.ho_w,
                                  'hide_b0': self.hide_b0, 'out_b0': self.out_b0, 'corrOrder': self.corrOrder,
                                  'pifsCorrValues': self.pifsCorrValues})
        else:
            print('Wrong Input!')


    def slot_buttonImgProcessMap(self):  # 过程监视
        #
        bpInNode = int(self.table_trainModelKey.item(0, 0).text())
        bpHideNode = int(self.table_trainModelKey.item(2, 0).text())
        bpOutNode = int(self.table_trainModelKey.item(3, 0).text())
        #
        # 获取inSam
        index = int(self.lineEdit_imgProcess.text())  # 横坐标Xi
        inSam = np.array(self.pifsValues)[:, index]
        #
        # 获取out_y0
        train_bp = ag.bpNet(bpInNode, bpHideNode, bpOutNode)
        train_bp.bpInitNetFunc()
        #
        if self.cmobox_rrnMethod.currentIndex() == 3:
            tt = index
            #
            out_yd = np.array(self.pifsValues)[:, 0]  # 真值为初始值
            outSam = []
            train_bp.ih_w = np.array(self.ih_w[tt]).astype(float)  # 定参数
            train_bp.ho_w = np.array(self.ho_w[tt]).astype(float)
            train_bp.out_b0 = np.array(self.out_b0[tt]).astype(float)
            train_bp.hide_b0 = np.array(self.hide_b0[tt]).astype(float)
            m_Insample = np.array(self.pifsValues)[:, index]
            for h in range(np.shape(np.array(m_Insample))[0]):
                train_bp.bpNetRecognizeFunc(m_Insample[h])
                outSam.extend(train_bp.out_y0.tolist())
            #
            print('DOY:', self.doys[index])
            print('Insam:', np.array(inSam))
            print('out_yd:', np.array(out_yd))
            print('out_y0:', np.array(outSam))

        if self.cmobox_rrnMethod.currentIndex() == 5:
            if self.corrOrder:
                corrOrder = self.corrOrder
            else:
                corrOrder = [0, 1, 6, 17, 20, 7, 16, 2, 15, 5, 3, 4, 19, 18, 14, 9, 13, 8, 11, 12, 10]
            self.lineEdit_corrOrder.setText(str(corrOrder))
            #
            m_Outsample = []
            m_Outsample.append(np.array(self.pifsValues)[:, 0])
            for i in range(1, len(corrOrder)):
                #
                # 获取out_yd:
                if index == corrOrder[i]:
                    out_yd = np.mean(m_Outsample, axis=0)  # 真值为均值
                    tt = corrOrder[i]
                    outSam = []
                    train_bp.ih_w = np.array(self.ih_w[tt]).astype(float)  # 定参数
                    train_bp.ho_w = np.array(self.ho_w[tt]).astype(float)
                    train_bp.out_b0 = np.array(self.out_b0[tt]).astype(float)
                    train_bp.hide_b0 = np.array(self.hide_b0[tt]).astype(float)
                    m_Insample = np.array(self.pifsValues)[:, tt]
                    for h in range(np.shape(np.array(m_Insample))[0]):
                        train_bp.bpNetRecognizeFunc(m_Insample[h])
                        outSam.extend(train_bp.out_y0.tolist())  # 此处必须要加tolist,不然结果会随时变化
                    ##
                    print('DOY:', self.doys[index])
                    print('Insam:', np.array(inSam))
                    print('out_yd:', np.array(out_yd))
                    print('out_y0:', np.array(outSam))
                    #
                    # lsm实际测试
                    p0 = [1, 20]
                    keys = leastsq(self.error, p0, args=(m_Insample, out_yd))[0]
                    #
                    outSam_lsm = np.round(m_Insample * keys[0] + keys[1], 5)
                    #
                    erro = np.sum((outSam_lsm - out_yd) * (outSam_lsm - out_yd)) / 2.0
                    print(erro)
                    break
                #
                tt = corrOrder[i]
                corrValue = []
                train_bp.ih_w = np.array(self.ih_w[tt]).astype(float)  # 定参数
                train_bp.ho_w = np.array(self.ho_w[tt]).astype(float)
                train_bp.out_b0 = np.array(self.out_b0[tt]).astype(float)
                train_bp.hide_b0 = np.array(self.hide_b0[tt]).astype(float)
                m_Insample = np.array(self.pifsValues)[:, tt]
                for h in range(np.shape(np.array(m_Insample))[0]):
                    train_bp.bpNetRecognizeFunc(m_Insample[h])
                    corrValue.extend(train_bp.out_y0.tolist())  # 此处必须要加tolist,不然结果会随时变化
                #
                m_Outsample.append(corrValue)  # 添加预测值作为参考值，保证局部最优
        #
        # 画图
        #
        self.progressFig = myFigure()
        m = []
        m.append(inSam)
        m.append(out_yd)
        m.append(outSam)
        if self.cmobox_rrnMethod.currentIndex() == 5:
            m.append(outSam_lsm)
        index222 = np.lexsort([np.array(m)[0, :]])
        m = np.array(m)[:, index222]
        plt.scatter(m[0, :], m[1, :], s=1, c='b')
        plt.plot(m[0, :], m[2, :], c='r')
        if self.cmobox_rrnMethod.currentIndex() == 5:
            plt.plot(m[0, :], m[3, :], c='g')
        self.progressFig.ax.set_title('DOY:%s' % self.doys[index])
        #
        self.scence = QtWidgets.QGraphicsScene()
        self.scence.addWidget(self.progressFig)
        self.view.setScene(self.scence)


    def slot_buttonTestSample(self):
        self.pifsTestValues = scipy.io.loadmat(self.lineEdit_inputPIFsMatDir.text())['PIFs_Refvalues']  # [num,23]
        print(np.shape(np.array(self.pifsTestValues)))
        self.lineEdit_testSample.setText(str(np.shape(np.array(self.pifsTestValues))[0]))
        #
        # 计算原始影像的RMSE
        rmse = np.zeros([len(self.doys), len(self.doys)])
        array_outSam = (np.array(self.pifsTestValues) + 0.1) / (2e-5)
        print(np.shape(array_outSam))  # eg:[21，12515]
        for mm in range(len(self.doys)):
            for nn in range(len(self.doys)):
                z0 = array_outSam[mm, :] - array_outSam[nn, :]
                rmse[mm, nn] = np.sqrt(np.mean(z0 * z0))
        #
        mean_rmse = np.mean(rmse)
        std_rmse = np.std(rmse)
        print("mean:{},std:{}".format(mean_rmse, std_rmse))
        #
        self.button_testBp.setDisabled(False)


    def slot_buttonTestBp(self):  # 输入测试集
        #
        self.pifsTestCorrValues = []
        #
        bpInNode = int(self.table_trainModelKey.item(0, 0).text())
        bpHideNode = int(self.table_trainModelKey.item(2, 0).text())
        bpOutNode = int(self.table_trainModelKey.item(3, 0).text())
        #
        train_bp = ag.bpNet(bpInNode, bpHideNode, bpOutNode)
        train_bp.bpInitNetFunc()
        #
        # 获取PIFS校正后的值
        if self.cmobox_contrastMethod.currentIndex() == 0:
            #
            outSam = []
            outSam.append(np.array(self.pifsTestValues)[:, 0])
            for tt in range(1, len(self.doys)):
                #
                train_bp.ih_w = np.array(self.ih_w[tt]).astype(float)  # 定参数
                train_bp.ho_w = np.array(self.ho_w[tt]).astype(float)
                train_bp.out_b0 = np.array(self.out_b0[tt]).astype(float)
                train_bp.hide_b0 = np.array(self.hide_b0[tt]).astype(float)
                #
                m_Insample = np.array(self.pifsTestValues)[:, tt]  # 输入数据
                col = []
                for h in range(np.shape(np.array(m_Insample))[0]):
                    train_bp.bpNetRecognizeFunc(m_Insample[h])
                    col.extend(train_bp.out_y0.tolist())
                #
                outSam.append(col)
        #
        self.pifsTestCorrValues = outSam
        print(np.shape(np.array(self.pifsTestCorrValues)))
        #
        pass


    def slot_buttonRMSECal(self):
        # 计算RMSE
        rmseDir = QtWidgets.QFileDialog.getSaveFileName(self, 'BPNet', './mat/', '*.mat')[0]
        self.lineEdit_rmseCal.setText(rmseDir)
        #
        if rmseDir:
            rmse = np.zeros([len(self.doys), len(self.doys)])
            array_outSam = (np.array(self.pifsTestCorrValues) + 0.1) / (2e-5)   # ref to DN
            print(np.shape(array_outSam))  # eg:[21，12515]
            for mm in range(len(self.doys)):
                for nn in range(len(self.doys)):
                    z0 = array_outSam[mm, :] - array_outSam[nn, :]
                    rmse[mm, nn] = np.sqrt(np.mean(z0 * z0))
            #
            mean_rmse = np.mean(rmse)
            std_rmse = np.std(rmse)
            print("mean:{},std:{}".format(mean_rmse, std_rmse))
            #
            # 保存路径
            scipy.io.savemat(rmseDir,
                             {'pifsTestCorrValues': self.pifsTestCorrValues, 'rmse': rmse, 'mean': mean_rmse,
                              'std': std_rmse})

    #
    def slot_buttonPredSample(self):
        #
        # 导入测试样本数据
        self.clipValues = scipy.io.loadmat(self.lineEdit_inputRefMatDir.text())['ref_Values']  # eg[21,1001,1001]
        print(np.shape(np.array(self.clipValues)))
        self.lineEdit_predSample.setText(str(np.shape(np.array(self.clipValues))))
        #
        self.button_predBP.setDisabled(False)


    def slot_buttonImportKeys(self):
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        self.ih_w = scipy.io.loadmat(open_filename)['ih_w']
        self.ho_w = scipy.io.loadmat(open_filename)['ho_w']
        self.out_b0 = scipy.io.loadmat(open_filename)['out_b0']
        self.hide_b0 = scipy.io.loadmat(open_filename)['hide_b0']
        print(np.shape(np.array(self.ih_w)))
        print(np.shape(np.array(self.ho_w)))
        print(np.shape(np.array(self.out_b0)))
        print(np.shape(np.array(self.hide_b0)))
        #
        self.button_imgProcessMap.setDisabled(False)


    def slot_buttonPredBp(self):
        #
        # 变量初始化
        bpInNode = int(self.table_trainModelKey.item(0, 0).text())
        bpHideNode = int(self.table_trainModelKey.item(2, 0).text())
        bpOutNode = int(self.table_trainModelKey.item(3, 0).text())
        #
        #
        if self.cmobox_rrnMethod.currentIndex() == 0:
            #
            self.correctedValues = []  # 校正后变量
            pred_bp = ag.bpNet(bpInNode, bpHideNode, bpOutNode)
            initIndex = 0
            #
            # 设定初始影像
            if self.cmobox_initValue.currentText() == '初始影像':
                initIndex = 0
            #
            if self.cmobox_initValue.currentText() == 'maxStds':
                pifStds = []
                for i in range(len(self.doys)):
                    pifValue = np.array(self.pifsValues)[:, i]
                    pifStd = np.std(pifValue)
                    pifStds.append(pifStd)
                maxStdIndex = np.argsort(pifStds)[-1]  # 获得映射
                initIndex = maxStdIndex
            #
            print(initIndex)
            #
            for tt in range(len(self.doys)):
                #
                corrValue = []
                if tt == initIndex:
                    corrValue = np.array(self.clipValues).astype(float)[tt, :, :]
                else:
                    pred_bp.ih_w = np.array(self.ih_w[tt]).astype(float)  # 定参数
                    pred_bp.ho_w = np.array(self.ho_w[tt]).astype(float)
                    pred_bp.out_b0 = np.array(self.out_b0[tt]).astype(float)
                    pred_bp.hide_b0 = np.array(self.hide_b0[tt]).astype(float)
                    train_img = np.array(self.clipValues).astype(float)[tt, :, :]
                    #
                    for i in range(np.shape(np.array(train_img))[0]):
                        col = []
                        for j in range(np.shape(np.array(train_img))[1]):
                            Ori_Values = train_img[i, j]
                            pred_bp.bpNetRecognizeFunc(Ori_Values)
                            col.extend(pred_bp.out_y0.tolist())
                        #
                        corrValue.append(col)
                    #
                print(np.shape(np.array(corrValue)))
                #
                self.correctedValues.append(corrValue)
            #
            print(np.shape(np.array(self.correctedValues)))

    #
    def slot_buttonBpStartDir(self):
        # 保存结果
        scipy.io.savemat(self.lineEdit_bpMatSaveDir.text(),
                         {'BP_CorrValues': self.correctedValues})
        pass

    def slot_buttonBpMatSaveDir(self):
        #
        # 导入BP的文件保存路径
        saveDir = QtWidgets.QFileDialog.getSaveFileName(self, 'BPNet', './mat/', '*.mat')[0]
        self.lineEdit_bpMatSaveDir.setText(saveDir)
        pass

    #
    def slot_buttonRMatInput(self):
        #
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        #
        if open_filename:
            if self.cmobox_matMode.currentIndex() == 0:  # 校正前（ref_Values）
                self.rData = scipy.io.loadmat(open_filename)['ref_Values']
            if self.cmobox_matMode.currentIndex() == 1:  # 校正后（BP_CorrValues）
                self.rData = scipy.io.loadmat(open_filename)['BP_CorrValues']
            #
            print(np.shape(np.array(self.rData)), np.array(self.rData)[0, 0, 0])  # eg: [21,1001,1001]
            self.lineEdit_rMatDir.setText(open_filename)

    def slot_buttonGMatInput(self):
        #
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        #
        if open_filename:
            if self.cmobox_matMode.currentIndex() == 0:  # 校正前（ref_Values）
                self.gData = scipy.io.loadmat(open_filename)['ref_Values']
            if self.cmobox_matMode.currentIndex() == 1:  # 校正后（BP_CorrValues）
                self.gData = scipy.io.loadmat(open_filename)['BP_CorrValues']
            #
            print(np.shape(np.array(self.gData)), np.array(self.gData)[0, 0, 0])
            self.lineEdit_gMatDir.setText(open_filename)
        else:
            print('NO Data!!!')

    def slot_buttonBMatInput(self):
        #
        open_filename = QtWidgets.QFileDialog.getOpenFileName(filter='*.mat')[0]
        #
        if open_filename:
            if self.cmobox_matMode.currentIndex() == 0:  # 校正前（ref_Values）
                self.bData = scipy.io.loadmat(open_filename)['ref_Values']
            if self.cmobox_matMode.currentIndex() == 1:  # 校正后（BP_CorrValues）
                self.bData = scipy.io.loadmat(open_filename)['BP_CorrValues']
            #
            print(np.shape(np.array(self.bData)), np.array(self.bData)[0, 0, 0])
            self.lineEdit_bMatDir.setText(open_filename)
        else:
            print('NO Data!!!')


    def slot_buttonRgbSaveDir(self):
        #
        rgbSaveDir = QtWidgets.QFileDialog.getExistingDirectory(self)
        dir = ("%s/" % rgbSaveDir)
        self.lineEdit_rgbSaveDir.setText(dir)
        #
        self.button_startConvert.setDisabled(False)


    def slot_buttonStartConvert(self):
        #
        rgbSaveDir = self.lineEdit_rgbSaveDir.text()
        rDataSet = np.array(self.rData)
        gDataSet = np.array(self.gData)
        bDataSet = np.array(self.bData)
        width = np.shape(rDataSet)[1]
        height = np.shape(rDataSet)[2]
        #
        for tt in range(len(self.doys)):
            rData = rDataSet[tt, :, :]
            gData = gDataSet[tt, :, :]
            bData = bDataSet[tt, :, :]
            #
            rData = dm.dataManagement().linearstretching(rData)
            gData = dm.dataManagement().linearstretching(gData)
            bData = dm.dataManagement().linearstretching(bData)

            #
            gtiff_driver = gdal.GetDriverByName('GTiff')
            gtiff_name = "%s/%s-%s.tif" % (rgbSaveDir, str(self.doys[tt]), str(self.cmobox_matMode.currentIndex()))
            out_ds = gtiff_driver.Create(gtiff_name,
                                         width,
                                         height,
                                         3,
                                         gdal.GDT_Byte)
            #
            # 存入1波段数据
            out_ds.GetRasterBand(3).WriteArray(bData)
            #
            # 存入2波段数据
            out_ds.GetRasterBand(2).WriteArray(gData)
            #
            # 存入3波段数据
            out_ds.GetRasterBand(1).WriteArray(rData)

            out_ds.FlushCache()
            #
            del out_ds
            pass


    #
    def slot_buttonVIsaveDir(self):
        viSaveDir = QtWidgets.QFileDialog.getSaveFileName(self, 'VI-Cal', './mat/', '*.mat')[0]
        self.lineEdit_viSaveDir.setText(viSaveDir)
        #
        self.button_viCal.setDisabled(False)
        pass

    def slot_buttonVICal(self):
        #
        viSaveDir = self.lineEdit_viSaveDir.text()
        NIR_refValues = np.array(self.gData)  # eg:(21,1001,1001)
        R_refValues = np.array(self.bData)
        viDatas = (NIR_refValues - R_refValues) / (NIR_refValues + R_refValues)
        print(np.shape(viDatas))
        #
        scipy.io.savemat(viSaveDir,{'NDVI_Values':viDatas})



class myView(QtWidgets.QGraphicsView):
    '''
    添加场景的窗口
    '''
    def __init__(self, *_args):
        super().__init__(*_args)
        self.zoomInFactor = 1.1
        self.zoomOutFactor = 1.0 / self.zoomInFactor
        self.factor = 1.0

    def keyPressEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Equal:
            self.scale(self.zoomInFactor, self.zoomInFactor)
            self.factor = self.factor * self.zoomInFactor
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Minus:
            self.scale(self.zoomOutFactor, self.zoomOutFactor)
            self.factor = self.factor * self.zoomOutFactor
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_0:
            # print(self.geometry())    # 放大缩小是变换了视角
            self.scale(1 / self.factor, 1 / self.factor)
            self.factor = 1.0
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_O:
            self.scale(0.4, 0.4)


class myFigure(FigureCanvas):
    '''
    提供一个载体，把弹出的figure给装载进取，然后获取句柄，就可以完成镶嵌
    '''

    def __init__(self, width=2.5, height=2, dpi=100):
        # 第一步：创建一个创建Figure
        self.fig = plt.figure(figsize=(width, height), dpi=dpi)
        # 第二步：在父类中激活Figure窗口
        super(myFigure, self).__init__(self.fig)  # 此句必不可少，否则不能显示图形
        # 第三步：创建一个子图，用于绘制图形用，111表示子图编号，如matlab的subplot(1,1,1)
        self.ax = self.fig.add_subplot(111)


