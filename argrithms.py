# -*- coding:utf-8 -*-
'''
主要功能：建立算法库，主要是储存与时间序列曲线匹配的算法程序
@ author: zhyin
@ time: 2019/09/20
'''

import numpy as np
import math
import matplotlib.pyplot as plt


### -*-LC8相关-*- ###

def dn_to_ref(values):
    '''
    完成DN值到反射率值的转化
    :param values: DN值 values
    :return: 反射率值 values
    '''
    values = np.array(values).astype(float)
    #
    multiple_reflectence = 2e-5
    add_reflectance = -0.1
    values[:, 1:] = values[:, 1:] * multiple_reflectence + add_reflectance
    values = values.tolist()
    #
    return values

#
# ANN
class bpNet(object):
    def __init__(self, BpInNode, BpHideNode, BpOutNode, imgNum=1, Greedy=False):
        #
        self.ih_w = np.zeros([BpInNode, BpHideNode])  # 隐含层结点权值
        self.ho_w = np.zeros([BpHideNode, BpOutNode])  # 输出层结点权值
        self.hide_b0 = np.zeros([BpHideNode])  # 隐含层结点阈值
        self.out_b0 = np.zeros([BpOutNode])  # 输出层结点阈值
        self.in_x0 = np.zeros([BpInNode])  # 输入向量值
        self.hide_s0 = np.zeros([BpHideNode])  # 隐含层结点值
        self.out_y0 = np.zeros([BpOutNode])  # 输出层结点值【预测值】
        self.outErr = np.zeros([BpOutNode])
        self.hideErr = np.zeros([BpHideNode])
        #
        self.rate_ih_w = 0.1  # 权值学习率（输入层->隐含层）
        self.rate_ho_w = 0.1  # 权值学习率（隐含层->输出层）
        self.rate_Hide_b0 = 0.1  # 阈值学习率（隐含层）
        self.rate_Out_b0 = 0.1  # 阈值学习率（输出层）
        self.totalErr = 1.0  # 允许的总误差
        #
        self.bpInNode = BpInNode  # 输入层结点数
        self.bpHideNode = BpHideNode  # 隐藏层结点数
        self.bpOutNode = BpOutNode  # 输出层结点数
        #
        if Greedy is False:
            self.out_yd = np.zeros([BpOutNode])  # 真值
        else:
            self.out_yd = np.zeros([imgNum, BpOutNode])

    def genc_randVal(self, low, high):  # 生成[low,high]之间的随机数
        import random
        var = random.random() * (high - low) + low
        return var

    def sigmoidFunc(self, t0):  # 激励函数
        m0 = math.exp(-t0)
        h0 = 1.0 / (1.0 + m0)
        return h0

    def winit(self, weight,dimension):
        if dimension == 1:
            for i in range(np.shape(weight)[0]):
                weight[i] = self.genc_randVal(-0.01, 0.01)
        if dimension == 2:
            for i in range(np.shape(weight)[0]):
                for j in range(np.shape(weight)[1]):
                    weight[i, j] = self.genc_randVal(-0.01, 0.01)

    def bpInitNetFunc(self):
        self.winit(self.ih_w,2)
        self.winit(self.ho_w,2)
        self.winit(self.hide_b0,1)
        self.winit(self.out_b0,1)

    def bpNetTrainFunc(self, InSam, OutSam, imgNum=1, Greedy=False,Ver=1):
        '''
        训练样本
        :param InSam: [8000]一维数组
        :param OutSam: [8000,1]二维数组
        '''
        #
        InSam = np.array(InSam).astype(float)
        OutSam = np.array(OutSam).astype(float)
        trainSample = np.shape(InSam)[0]
        self.totalErr = 0  # 总的误差
        sum = 0  # 和
        z0 = 0  # 激活值
        #
        for isamp in range(trainSample):
            #
            # 输入层 eg:[8000] or [8000,bpInNode]
            if self.bpInNode == 1:
                self.in_x0[0] = InSam[isamp]
            else:
                self.in_x0 = InSam[isamp, :]  # 输入的样本值
            #
            # 输出层
            if Greedy is True and Ver == 1:  # 贪婪算法中输出值 eg[imgNum,isamp] or [imgNum,isamp,bpOutNode]
                if self.bpOutNode == 1:
                    self.out_yd[:,0] = OutSam[:, isamp]
                else:
                    self.out_yd = OutSam[:, isamp, :]  # 期待输出的样本值
            if Greedy is False and Ver == 1:
                if self.bpOutNode == 1:
                    self.out_yd[0] = OutSam[isamp]
                else:
                    self.out_yd = OutSam[isamp, :]  # 期待输出的样本值
            #
            if Greedy is False and Ver ==2:    # Ver2.0版本中真值有所变化:[bpOutNode,isamp]
                self.out_yd = OutSam[:,isamp]  # 期待输出的样本值
            #
            # 正向传播的过程
            # 1）输入层->隐含层1
            for j in range(self.bpHideNode):
                sum = 0.0
                for i in range(self.bpInNode):
                    sum += self.ih_w[i, j] * self.in_x0[i]
                z0 = sum + self.hide_b0[j]
                self.hide_s0[j] = self.sigmoidFunc(z0)  # 隐含层各个单元的输出 1.0/( 1.0 + exp(-z0))
            #
            # 2) 隐含层->输出层
            for j in range(self.bpOutNode):
                sum = 0.0
                for i in range(self.bpHideNode):
                    sum += self.ho_w[i, j] * self.hide_s0[i]
                z0 = sum + self.out_b0[j]
                self.out_y0[j] = self.sigmoidFunc(z0)  # 输出层各个单元的输出 1.0/(1.0 + exp(-z0)
            #
            # 误差反向传播：对于网络中每个输出单元，计算误差值，更新权值
            # 1）输出层->隐含层
            sum = 0.0
            # 计算总均方差
            for j in range(self.bpOutNode):
                #
                # 引入贪婪算法，则此处需要修改
                if Greedy is False:
                    z0 = self.out_yd[j] - self.out_y0[j]
                    self.outErr[j] = z0
                    sum += z0 * z0
                if Greedy is True and Ver == 1:
                    h = 0.0
                    sum = 0.0
                    for m in range(imgNum):
                        h += self.out_yd[m,j] - self.out_y0    # 理论上进行求导
                        sum += (self.out_yd[m,j] - self.out_y0) * (self.out_yd[m,j] - self.out_y0)
                    z0 = h
                    self.outErr[j] = z0
            #
            self.totalErr += sum / 2.0
            #
            for j in range(self.bpOutNode):
                self.outErr[j] = self.outErr[j] * \
                                 self.out_y0[j] * (1.0 - self.out_y0[j])  # 输出层δ2 = ei * θ'(si2)  期望误差*输出层Outy0激励函数导数
                for i in range(self.bpHideNode):
                    self.ho_w[i,j] += self.rate_ho_w * self.outErr[j] * self.hide_s0[i]      # 更新权重
            for j in range(self.bpOutNode):
                self.out_b0[j] += self.rate_Out_b0 * self.outErr[j]     # 更新阈值
            #
            # 2) 隐含层->输入层
            for j in range(self.bpHideNode):
                sum = 0.0
                for i in range(self.bpOutNode):
                    sum += self.outErr[i] * self.ho_w[j,i]
                self.hideErr[j] = sum * self.hide_s0[j] * (1. - self.hide_s0[j]) #隐含层δ1 = （∑out_Er *ho_w） * θ'(si2)  隐含层误差*隐含层Hides0激励函数导数
                for i in range(self.bpInNode):
                    self.ih_w[i,j] += self.rate_ih_w * self.hideErr[j] * self.in_x0[i]  # 更新权重
            for j in range(self.bpHideNode):
                self.hide_b0[j] += self.rate_Hide_b0 * self.hideErr[j]  # 更新阈值

    def bpNetRecognizeFunc(self,testSam):
        '''
        BP神经网络测试样本
        :param testSam: 测试样本
        :return:
        '''
        testSam = np.array(testSam).astype(float)
        # self.totalErr = 0  # 单个样本的误差
        #
        # 输入层 eg:[8000] or [8000,bpInNode]
        if self.bpInNode == 1:
            self.in_x0[0] = testSam
        else:
            self.in_x0 = testSam  # 输入的样本值
        #
        # 输入->隐含层
        for j in range(self.bpHideNode):
            sum = 0.0
            for i in range(self.bpInNode):
                sum += self.ih_w[i, j] * self.in_x0[i]
            z0 = sum + self.hide_b0[j]
            self.hide_s0[j] = self.sigmoidFunc(z0)  # 隐含层各个单元的输出 1.0/( 1.0 + exp(-z0))
        #
        # 2) 隐含层->输出层
        for j in range(self.bpOutNode):
            sum = 0.0
            for i in range(self.bpHideNode):
                sum += self.ho_w[i, j] * self.hide_s0[i]
            z0 = sum + self.out_b0[j]
            self.out_y0[j] = self.sigmoidFunc(z0)  # 输出层各个单元的输出 1.0/(1.0 + exp(-z0)
        #
    pass

#
# demo测试
if __name__ == "__main__":
    file = open('./txt/bpTest.txt','w')
    err = []
    err_time = []
    m_Insample = [[1.78, 1.14], [1.96, 1.18], [1.86, 1.20], [1.72, 1.24], [2.00, 1.26], [2.00, 1.28], [1.96, 1.30],
                  [1.74, 1.36], [1.64, 1.38], [1.82, 1.38], [1.90, 1.38], [1.70, 1.40], [1.82, 1.48], [1.82, 1.54],
                  [2.08, 1.56]]
    m_Outsample = [1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    m_Tsample = [[1.80,1.24],[1.84,1.28],[2.04,1.40]]
    # m_Insample = [[1.16,0.116],[1.35,0.104],[1.72,0.078],[1.86,0.107],[1.97,0.136],[2.15,0.082],[2.23,0.125],
    #               [2.48,0.076],[2.79,0.122],[2.85,0.092],[3.07,0.081],[3.45,0.068],[3.59,0.077],[3.80,0.108],
    #               [3.93,0.128],[4.14,0.063],[4.46,0.135],[4.55,0.070],[4.84,0.126],[5.03,0.087]]
    # m_Outsample = [0.502,0.595,0.588,0.662,0.655,0.645,0.736,0.764,0.785,0.792,0.814,0.903,0.931,0.982,0.973,0.981,0.973,0.988,0.969,0.986]
    # m_Tsample = [[1.42,0.086],[2.51,0.071],[3.21,0.107],[4.29,0.096],[5.24,0.065]]
    #
    bp = bpNet(BpInNode=2,BpHideNode=10,BpOutNode=1)
    bp.bpInitNetFunc()

    # 训练
    times = 0
    while bp.totalErr > 0.0001 and times < 10000:
        times += 1
        bp.bpNetTrainFunc(m_Insample,m_Outsample)
        if (times + 1) % 100 == 0:
            file.write('BP %5d DT:%10.5f\n' % ((times+1),bp.totalErr))
            print('BP %5d DT:%10.5f\n' % ((times+1),bp.totalErr))
        err.append(bp.totalErr)
        err_time.append(times+1)
    plt.plot(err_time,err)
    plt.show()
    # 测试
    testSample = np.shape(np.array(m_Tsample))[0]
    for j in range(testSample):
        bp.bpNetRecognizeFunc(np.array(m_Tsample)[j,:])
        print(bp.out_y0)
    pass