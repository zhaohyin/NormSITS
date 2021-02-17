# -*- coding:utf-8 -*- #
'''
    功能：GUI界面设计
'''
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QDialog
import gdal, osr
import data_manager as dm
import about_txt as at
import cWnd_LD, cWnd_LT
import pixel_extract as pext
#

class mainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        #
        self.posX = 0
        self.posY = 0
        self.currentImgDir = []
        #
        self.initUI()
        #
        # 头文件变量
        self.openfile_name = []  # 头文件的地址
        self.infos = {}  # 头文件信息
        self.bandNames = []  # 波段名
        self.mode = 'M'  # 波段选择的模式
        self.count = 0
        #
        # 坐标映射相关变量
        self.extend = []  # 仿射矩阵
        self.pcs = []  # 地图投影信息
        self.sr = []
        self.gcs = []
        self.imgWidth = 0
        self.imgHeight = 0

    def initUI(self):
        '''
        初始化主窗口
        '''
        # 新建主窗口
        self.setObjectName("mainWindow")
        self.setWindowModality(QtCore.Qt.WindowModal)  # 设置窗口
        self.resize(800, 600)
        self.setWindowTitle("NormSITS")
        #
        # 菜单栏
        menubar = QtWidgets.QMenuBar(self)
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu("&File")
        lcDataMenu = menubar.addMenu("&LD")
        lcTsExMenu = menubar.addMenu('&LT')
        #
        # 添加动作
        # File:
        openAct = QtWidgets.QAction('&Open', self)
        exitAct = QtWidgets.QAction('&Exit', self)
        mtlPropAct = QtWidgets.QAction('&MTL_Prop[NULL]',self)   # MTL文件的属性批阅读
        fileMenu.addAction(openAct)
        fileMenu.addAction(exitAct)
        fileMenu.addAction(mtlPropAct)
        #
        # LcDataMenu：
        downloadAct = QtWidgets.QAction('&Download Data', self)
        btoolAct = QtWidgets.QAction('&clip', self)
        combAct = QtWidgets.QAction('&Band Combination', self)
        lcDataMenu.addAction(downloadAct)  # 下载LANDSAT数据
        lcDataMenu.addAction(combAct)  # 波段合成
        lcDataMenu.addAction(btoolAct)  # 基本工具
        #
        # lcTsExMenu:
        pifAct = QtWidgets.QAction('&PIFs Select', self)
        lcTsExMenu.addAction(pifAct)
        tsrrnAct = QtWidgets.QAction('&NMAG', self)   # 相对辐射校正方法初探
        lcTsExMenu.addAction(tsrrnAct)
        #
        # 添加控件
        self.tree_layer = QtWidgets.QTreeWidget(self)  # 图层列表
        self.table_info = QtWidgets.QTableWidget(self)  # 显示图像信息
        self.table_bandChoose = QtWidgets.QTableWidget(self)  # 显示波段信息
        self.button_singleBand = QtWidgets.QPushButton('S', self)  # 单波段
        self.button_multiBand = QtWidgets.QPushButton('M', self)  # 多波段
        self.button_display = QtWidgets.QPushButton('D', self)  # 显示遥感影像
        self.cmobox_LMode = QtWidgets.QComboBox(self)  # 线性变换的模式
        self.table_pos = QtWidgets.QTableWidget(self)  # 显示行列号和经纬度
        self.button_r2p = QtWidgets.QPushButton('R->P', self)
        self.button_l2p = QtWidgets.QPushButton('L->P', self)  # 寻找中心样本点
        #
        # # 添加场景
        self.myscene = myscene()
        self.graphic_rsData = myView(self)  # 显示遥感影像

        #
        # 控件初始化
        self.tree_layer.setHeaderLabels(['Layers'])
        self.table_info.horizontalHeader().hide()
        self.table_pos.horizontalHeader().hide()

        self.tree_layer.setColumnWidth(0, 1000)  # 设置列宽
        self.table_bandChoose.setColumnCount(1)  # 设置行列数
        self.table_bandChoose.setHorizontalHeaderLabels(['Bands'])
        self.table_bandChoose.setRowCount(3)
        self.table_bandChoose.setVerticalHeaderLabels(['R', 'G', 'B'])
        self.table_bandChoose.setItem(0, 0, QtWidgets.QTableWidgetItem('B7.tif'))
        self.table_bandChoose.setItem(1, 0, QtWidgets.QTableWidgetItem('B5.tif'))
        self.table_bandChoose.setItem(2, 0, QtWidgets.QTableWidgetItem('B4.tif'))
        self.table_pos.setColumnCount(1)
        self.table_pos.setRowCount(4)
        for i in range(4):
            self.table_pos.setRowHeight(i, 27)
            self.table_pos.setItem(i, 0, QtWidgets.QTableWidgetItem(str(0)))
        self.table_pos.setVerticalHeaderLabels(['Row', 'Col', 'Lon', 'Lat'])
        self.cmobox_LMode.addItems(['Rapid', 'Slow'])

        #
        # 绝对布局
        menubar.setGeometry(10, 10, 780, 30)
        self.tree_layer.setGeometry(10, 50, 110, 370)
        self.table_bandChoose.setGeometry(10, 430, 110, 110)
        self.button_singleBand.setGeometry(10, 550, 30, 20)
        self.button_multiBand.setGeometry(50, 550, 30, 20)
        self.button_display.setGeometry(90, 550, 30, 20)
        self.cmobox_LMode.setGeometry(130, 550, 100, 20)

        self.graphic_rsData.setGeometry(130, 50, 660, 370)

        self.table_info.setGeometry(130, 430, 270, 110)
        self.table_pos.setGeometry(410, 430, 110, 110)
        self.button_r2p.setGeometry(410, 550, 50, 20)
        self.button_l2p.setGeometry(470, 550, 50, 20)

        #
        # 菜单动作响应
        openAct.setShortcut(QtGui.QKeySequence('Ctrl+O'))
        openAct.setStatusTip("Open a file.")
        openAct.triggered.connect(self.openfile)

        exitAct.setShortcut(QtGui.QKeySequence('Ctrl+Q'))
        exitAct.setStatusTip("Close a file.")
        exitAct.triggered.connect(QtWidgets.qApp.exit)

        mtlPropAct.setShortcut(QtGui.QKeySequence('Ctrl+m'))
        mtlPropAct.setStatusTip('Read MTLtxt Prop.')
        mtlPropAct.triggered.connect(self.readMtlProp)     # 功能尚未展开
        #
        self.landsatDown = cWnd_LD.landsatDataDownUI()
        downloadAct.triggered.connect(self.landsatDown.show)
        self.landsatCombination = cWnd_LD.landsatbandCombination()
        combAct.triggered.connect(self.landsatCombination.show)
        self.bt = cWnd_LD.landsatDataClipUI()
        btoolAct.triggered.connect(self.bt.show)
        #
        self.pif = cWnd_LT.landsatPIFsUI()
        pifAct.triggered.connect(self.pif.show)
        self.tsrrn = cWnd_LT.landsatTSRRNormalizationUI()
        tsrrnAct.triggered.connect(self.tsrrn.show)
        #
        # 事件响应
        self.tree_layer.clicked.connect(self.slot_treelayerClick)
        self.button_singleBand.clicked.connect(self.slot_bottonSingleMode)
        self.button_multiBand.clicked.connect(self.slot_buttonMultiMode)
        self.button_display.clicked.connect(self.slot_buttonDisplay)
        self.button_r2p.clicked.connect(self.slot_buttonR2P)
        self.button_l2p.clicked.connect(self.slot_buttonL2P)

        # 显示
        self.show()

    #
    # 槽函数
    #
    def openfile(self):
        self.openfile_name = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        self.slot_treeLayer()
        self.slot_tableInfo()

    def readMtlProp(self):   # 批获取遥感影像MTL文件中的某一属性【很实用的一个功能】
        landsatDir = "%s/" % QtWidgets.QFileDialog.getExistingDirectory(self)
        CLOUD_COVER = []
        import os
        for roots, dirs, files in os.walk(landsatDir):
            #
            # 规定读取顺序
            order_list = ['LTCP0123456789_t']
            someorder = {letter: val for val, letter in enumerate(order_list[0])}
            new_dirs = sorted(dirs, key=lambda x: [someorder.get(letter) for letter in x])
            #
            for dir in new_dirs:
                if "L" in dir:
                    MTL_dir = "%s%s/" % (landsatDir, dir)
                    MTL_name = "%s_MTL.txt" % (dir)
                    MTL_path = os.path.join(MTL_dir, MTL_name)
                    #
                    _, infos = at.readHeader().readMTLtxt(MTL_path)
                    CLOUD_COVER.append(infos['CLOUD_COVER'])
        #
        print(CLOUD_COVER)
        #


    def slot_treeLayer(self):
        #
        # MTL头文件读取，获取影像信息和影像名称
        if self.openfile_name[-7:] == 'MTL.txt':
            #
            self.bandNames, self.infos = at.readHeader().readMTLtxt(self.openfile_name)
            #
            # 添加节点
            fatherNode = QtWidgets.QTreeWidgetItem(self.tree_layer)
            fatherNode.setText(0, '%s' % (self.openfile_name[:-8]))
            #
            self.currentImgDir = self.openfile_name[:-8]
            for bandName in self.bandNames:
                childNode = QtWidgets.QTreeWidgetItem(fatherNode)
                childNode.setText(0, bandName[41:])
        #
        # 读取TIFF数据，获取影像的长和宽
        if self.openfile_name[-4:] == '.tif' or self.openfile_name[-4:] == '.TIF':
            #
            self.myscene = myscene()
            #
            dataset = gdal.Open(self.openfile_name)
            #
            # 加载投影信息,全部设置为私有变量
            self.extend = dataset.GetGeoTransform()  # 仿射矩阵
            self.pcs = dataset.GetProjection()  # 地图投影信息
            self.sr = osr.SpatialReference()
            self.sr.ImportFromWkt(self.pcs)
            self.gcs = self.sr.CloneGeogCS()
            self.imgWidth = dataset.RasterXSize
            self.imgHeight = dataset.RasterYSize
            #
            img = QtGui.QImage(self.openfile_name).scaled(self.imgWidth, self.imgHeight)
            self.myscene.addPixmap(QtGui.QPixmap.fromImage(img))
            self.graphic_rsData.setScene(self.myscene)
            #
            pass

    def slot_tableInfo(self):
        '''
        列表显示遥感影像的属性
        '''
        if self.openfile_name[-7:] == 'MTL.txt':
            #
            i = 0
            labels = []
            #
            self.table_info.setRowCount(len(self.infos))
            self.table_info.setColumnCount(1)
            for info in self.infos:
                self.table_info.setItem(i, 0, QtWidgets.QTableWidgetItem(self.infos[info]))
                labels.append(info)
                i = i + 1
            self.table_info.setVerticalHeaderLabels(labels)
        #
        if self.openfile_name[-4:] == '.tif' or self.openfile_name[-4:] == '.TIF':
            self.table_info.setRowCount(3)
            self.table_info.setColumnCount(1)
            self.table_info.setVerticalHeaderLabels(['TIME', 'WIDTH', 'HEIGHT'])
            self.table_info.setItem(0, 0, QtWidgets.QTableWidgetItem(str(self.openfile_name[-12:-4])))
            self.table_info.setItem(1, 0, QtWidgets.QTableWidgetItem(str(self.imgWidth)))
            self.table_info.setItem(2, 0, QtWidgets.QTableWidgetItem(str(self.imgHeight)))

    def slot_treelayerClick(self):
        '''
        获取节点的名称，从而进行后续的图像显示
        '''
        str = self.tree_layer.currentItem().text(0)
        self.currentImgDir = self.tree_layer.currentItem().parent().text(0)
        if self.mode == "S":
            self.table_bandChoose.setItem(0, 0, QtWidgets.QTableWidgetItem(str))
        if self.mode == "M":
            self.table_bandChoose.setItem(self.count, 0, QtWidgets.QTableWidgetItem(str))
            self.count = (self.count + 1) % 3

    def slot_bottonSingleMode(self):
        #
        # 单波段列表显示
        #
        self.mode = 'S'
        self.table_bandChoose.setColumnCount(1)
        self.table_bandChoose.setRowCount(1)
        self.table_bandChoose.setVerticalHeaderLabels(['GRAY'])

    def slot_buttonMultiMode(self):
        #
        # 多波段列表显示
        #
        self.mode = 'M'
        self.table_bandChoose.setColumnCount(1)
        self.table_bandChoose.setRowCount(3)
        self.table_bandChoose.setVerticalHeaderLabels(['R', 'G', 'B'])
        self.count = 0

    def slot_buttonDisplay(self):
        '''
        显示遥感影像，鼠标位置的响应
        '''
        #
        self.myscene = myscene()
        #
        if self.mode == 'M':
            R_DIR = ('%s_%s' % (self.currentImgDir, self.table_bandChoose.item(0, 0).text()))
            G_DIR = ('%s_%s' % (self.currentImgDir, self.table_bandChoose.item(1, 0).text()))
            B_DIR = ('%s_%s' % (self.currentImgDir, self.table_bandChoose.item(2, 0).text()))
            #
            rgb_tiffPath = "/Volumes/KINGSTON/rgbtiff/%s_%s%s%s.tif" % (B_DIR[-47:-7], R_DIR[-5], G_DIR[-5], B_DIR[-5])
            if os.path.exists(rgb_tiffPath) is False:
                dm.landsatData()._rgbCombination(rgb_tiffPath, R_DIR, G_DIR, B_DIR, self.cmobox_LMode.currentText())
            #
            dataset = gdal.Open(rgb_tiffPath)
            #
            # 加载投影信息,全部设置为私有变量
            self.extend = dataset.GetGeoTransform()  # 仿射矩阵
            self.pcs = dataset.GetProjection()  # 地图投影信息
            self.sr = osr.SpatialReference()
            self.sr.ImportFromWkt(self.pcs)
            self.gcs = self.sr.CloneGeogCS()
            self.imgWidth = dataset.RasterXSize
            self.imgHeight = dataset.RasterYSize
            #
            img = QtGui.QImage(rgb_tiffPath).scaled(self.imgWidth, self.imgHeight)
            self.myscene.addPixmap(QtGui.QPixmap.fromImage(img))
            self.graphic_rsData.setScene(self.myscene)
            #
        #
        if self.mode == 'S':
            #
            R_DIR = ('%s_%s' % (self.currentImgDir, self.table_bandChoose.item(0, 0).text()))
            # #
            gray_tiffPath = "/Volumes/KINGSTON/graytiff/%s_%s%s%s.tif" % (
            R_DIR[-47:-7], R_DIR[-5], R_DIR[-5], R_DIR[-5])
            if os.path.exists(gray_tiffPath) is False:
                dm.landsatData()._rgbCombination(R_DIR, R_DIR, R_DIR, self.cmobox_LMode.currentText())
            # gray_tiffPath = './datasat/ss.tif'
            #
            dataset = gdal.Open(gray_tiffPath)
            #
            # 加载投影信息,全部设置为私有变量
            self.extend = dataset.GetGeoTransform()  # 仿射矩阵
            self.pcs = dataset.GetProjection()  # 地图投影信息
            self.sr = osr.SpatialReference()
            self.sr.ImportFromWkt(self.pcs)
            self.gcs = self.sr.CloneGeogCS()
            self.imgWidth = dataset.RasterXSize
            self.imgHeight = dataset.RasterYSize
            #
            img = QtGui.QImage(gray_tiffPath).scaled(self.imgWidth, self.imgHeight)
            self.myscene.addPixmap(QtGui.QPixmap.fromImage(img))
            self.graphic_rsData.setScene(self.myscene)

    def slot_buttonR2P(self):
        '''
        定位：Row,Col ---> Pix && Lon,Lat
        '''
        #
        if self.myscene.addItemFlag:
            self.myscene.removeItem(self.myscene.item1)
            self.myscene.removeItem(self.myscene.item2)
        #
        row = int(self.table_pos.item(0, 0).text())
        col = int(self.table_pos.item(1, 0).text())
        x, y = pext.rowcol_to_xy(self.extend, col, row)  ## 注意这里是COL，ROW
        lon, lat = pext.xy_to_lonlat(self.gcs, self.sr, x, y)
        self.table_pos.setItem(2, 0, QtWidgets.QTableWidgetItem(str(lon)))
        self.table_pos.setItem(3, 0, QtWidgets.QTableWidgetItem(str(lat)))
        #
        # 定位（两个坐标系统完全不一样的）
        x = col
        y = row
        self.graphic_rsData.centerOn(x, y)
        self.myscene.item1.setLine(x - 10, y, x + 10, y)
        self.myscene.item2.setLine(x, y - 10, x, y + 10)
        self.myscene.addItemFlag = True
        #
        self.myscene.addItem(self.myscene.item1)
        self.myscene.addItem(self.myscene.item2)

    def slot_buttonL2P(self):
        '''
        定位：Lon，Lat -----> Pix && Row,Col
        '''
        #
        if self.myscene.addItemFlag:
            self.myscene.removeItem(self.myscene.item1)
            self.myscene.removeItem(self.myscene.item2)
        #
        lon = float(self.table_pos.item(2, 0).text())
        lat = float(self.table_pos.item(3, 0).text())
        x, y, _ = pext.lonlat_to_xy(self.gcs, self.sr, lon, lat)
        row, col = pext.xy_to_rowcol(self.extend, x, y)
        self.table_pos.setItem(0, 0, QtWidgets.QTableWidgetItem(str(row)))
        self.table_pos.setItem(1, 0, QtWidgets.QTableWidgetItem(str(col)))
        #
        #
        # 定位（两个坐标系统完全不一样的）
        x = col
        y = row
        self.graphic_rsData.centerOn(x, y)
        self.myscene.item1.setLine(x - 10, y, x + 10, y)
        self.myscene.item2.setLine(x, y - 10, x, y + 10)
        self.myscene.addItemFlag = True
        #
        self.myscene.addItem(self.myscene.item1)
        self.myscene.addItem(self.myscene.item2)

        pass


class myView(QtWidgets.QGraphicsView):
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


class myscene(QtWidgets.QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.initVar()

    def initVar(self):
        # 定义私有变量
        self.row = 0
        self.col = 0
        self.lon = 0
        self.lat = 0
        self.posX = 0
        self.posY = 0
        self.addItemFlag = False
        self.item1 = myLineItem()
        self.item2 = myLineItem()
        self.menu = QtWidgets.QMenu()
        self.action_wpSave = QtWidgets.QAction('&Save to WB point', self)
        self.action_vpSave = QtWidgets.QAction('&Save to VS point', self)
        #
        # 定义槽和信号
        self.action_wpSave.triggered.connect(self.slot_actionWpSave)
        self.action_vpSave.triggered.connect(self.slot_actionVpSave)

    def slot_actionWpSave(self):
        '''
        右键菜单添加白板点
        '''
        rowindex = int(mainWindow.wbCorr_Exp.table_wbList.rowCount())
        mainWindow.wbCorr_Exp.table_wbList.setRowCount(rowindex + 1)
        mainWindow.wbCorr_Exp.table_wbList.setItem(rowindex, 0,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(2, 0)))
        mainWindow.wbCorr_Exp.table_wbList.setItem(rowindex, 1,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(3, 0)))
        mainWindow.wbCorr_Exp.table_wbList.setItem(rowindex, 2,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(0, 0)))
        mainWindow.wbCorr_Exp.table_wbList.setItem(rowindex, 3,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(1, 0)))
        for i in range(4):
            mainWindow.wbCorr_Exp.table_wbList.item(rowindex, i).setTextAlignment(QtCore.Qt.AlignCenter)
        pass

    def slot_actionVpSave(self):
        '''
        右键菜单添加验证点
        '''
        rowindex = int(mainWindow.wbCorr_Exp.table_vsList.rowCount())
        mainWindow.wbCorr_Exp.table_vsList.setRowCount(rowindex + 1)
        mainWindow.wbCorr_Exp.table_vsList.setItem(rowindex, 0,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(2, 0)))
        mainWindow.wbCorr_Exp.table_vsList.setItem(rowindex, 1,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(3, 0)))
        mainWindow.wbCorr_Exp.table_vsList.setItem(rowindex, 2,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(0, 0)))
        mainWindow.wbCorr_Exp.table_vsList.setItem(rowindex, 3,
                                                   QtWidgets.QTableWidgetItem(mainWindow.table_pos.item(1, 0)))
        for i in range(4):
            mainWindow.wbCorr_Exp.table_vsList.item(rowindex, i).setTextAlignment(QtCore.Qt.AlignCenter)
        pass

    def mousePressEvent(self, event):
        #
        if event.button() == QtCore.Qt.LeftButton:
            if self.addItemFlag:
                self.removeItem(self.item1)
                self.removeItem(self.item2)
            #
            self.row = int(event.scenePos().y())
            self.col = int(event.scenePos().x())
            self.posX = int(event.scenePos().x())
            self.posY = int(event.scenePos().y())

            # print(self.row, self.col)
            mainWindow.table_pos.setItem(0, 0, QtWidgets.QTableWidgetItem(str(self.row)))
            mainWindow.table_pos.setItem(1, 0, QtWidgets.QTableWidgetItem(str(self.col)))

            x, y = pext.rowcol_to_xy(mainWindow.extend, self.col, self.row)  ## 注意这里是COL，ROW
            self.lon, self.lat = pext.xy_to_lonlat(mainWindow.gcs, mainWindow.sr, x, y)
            mainWindow.table_pos.setItem(2, 0, QtWidgets.QTableWidgetItem(str(self.lon)))
            mainWindow.table_pos.setItem(3, 0, QtWidgets.QTableWidgetItem(str(self.lat)))

            self.item1.setLine(self.posX - 10, self.posY, self.posX + 10, self.posY)
            self.item2.setLine(self.posX, self.posY - 10, self.posX, self.posY + 10)
            self.addItemFlag = True

            self.addItem(self.item1)
            self.addItem(self.item2)

        if event.button() == QtCore.Qt.RightButton:
            pass
        pass

    def contextMenuEvent(self, event):
        self.menu.addAction(self.action_wpSave)
        self.menu.addAction(self.action_vpSave)
        self.menu.exec(event.screenPos())
        pass


class myLineItem(QtWidgets.QGraphicsLineItem):
    def __init__(self, parent=None):
        super().__init__()
        self.initItem()

    def initItem(self):
        pen = QtGui.QPen()
        pen.setWidth(1)
        pen.setColor(QtCore.Qt.red)
        self.setPen(pen)
        pass


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = mainWindowUI()
    sys.exit(app.exec())
