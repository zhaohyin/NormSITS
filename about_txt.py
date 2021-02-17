# -*- coding:utf-8 -*-
'''
主要功能：读取TXT文件
'''
#
# MTL.txt读取规范
class readHeader(object):

    def __init__(self):
        #
        # 私有变量
        self.file_Names = []  # 记录波段数据的文件名
        self.infos = {'CLOUD_COVER': '0', 'GRID_CELL_SIZE_REFLECTIVE': '0', 'MAP_PROJECTION': 'none', 'DATUM': 'none', 'DATE_ACQUIRED': 'none',
                     'REFLECTIVE_LINES': '0', 'REFLECTIVE_SAMPLES': '0'}
        pass

    def readMTLtxt(self,MTLDIR):
        '''
        写入MTL文本文件的
        :param MTLDIR：MTL头文件文件路径
        :return: file_Name
        '''
        #
        # 初始化变量
        self.file_Names = []
        #
        txt = open(MTLDIR,'r')
        lines = txt.readlines()
        for line in lines:
            strv = line.split()
            if 'FILE_NAME_BAND' in strv[0]:
                self.file_Names.append(strv[2][1:-1])
            for info in self.infos:
                if info in strv[0]:
                    self.infos[info] = strv[2]
        #
        return self.file_Names,self.infos
    pass


