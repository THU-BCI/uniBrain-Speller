#!/usr/bin/env python
# _*_ coding: utf-8 _*_

import socket
import threading
import math
import numpy as np
from collections import deque
from scipy import signal
from loguru import logger
from .NeuroScanMessage import NeuroScanMessage
import matplotlib.pyplot as plt

class NeuroScanEEGThread(threading.Thread,):
    def __init__(self, config=None,hostname='0.0.0.0', port=4000,threadName='NeuroScanEEG', device='NeuroScan', n_chan=2, record_srate=1000,srate=250,keepEvent=False):

        threading.Thread.__init__(self)
        if config is not None:
            self.n_chan = config.chnNUM
            self.port = config.streaming_port
            self.hostname = config.streaming_ip
            self.record_srate = config.record_srate
            self.srate = config.srate
        else:
            self.n_chan = n_chan
            self.port = port
            self.hostname = hostname
            self.record_srate = record_srate  # 原始数据采样率
            self.srate = srate


        self.name = threadName
        self.sock = []
        self.device = device
        # cash 数据和event缓存
        self.event = None
        self.eventPoint = deque(maxlen=15000)
        self.eventExist = None
        # 是否保持事件
        self.keepEvent = keepEvent

        # package 是要发送的数据包
        self.package = None
        self.logger = logger
        self.lock = threading.RLock()
        self.messageQueue = deque(maxlen=360000)  # 缓冲的数据队列
        self.track = deque(maxlen=360000)
        self.packetSize = int(self.record_srate * 0.1)
        self.downSize = int(self.srate * 0.1)
        self.filters = self._initFilter()
        

        
    def run(self):
        """
        线程开始函数
        """
        self.read_thread()

    def read_thread(self):  # visit eegthread, catch sockets and parse sockets, append parsed data to ringbuffer

        # 请求获得基本信号：通道数目，采样率和数据包大小
        self.requestInfo()
        # 请求导联信息
        self.requestChannelInfo()

        socket_lock = threading.Lock()

        while self.shutdown_flag.isSet():
            if not self.sock:
                break
            socket_lock.acquire()

            if not self.sock:
                socket_lock.release()
                break
            try:
                # 接收数据 message中包含数据类型等信s息
                self.requestEEG(self.sock)
            except:
                socket_lock.release()
                self.sock.close()
            else:

                wholepacket,startData = self._addEvent()

                if wholepacket is not None:
                    self.messageQueue.append(wholepacket)
                    self.track.append(startData)
                else:
                    pass

                socket_lock.release()

    def connect(self):
        """
        try to connect data server
        """
        # 开启信息交换监听功能
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        notconnect = True
        reconnecttime = 0  # 未连接次数
        while notconnect:
            try:
                self.sock.connect((self.hostname, self.port))
                notconnect = False
                self.logger.info('Data server connected')
            except:
                reconnecttime += 1
                self.logger.info('connection failed, retrying for {} times', reconnecttime)
                if reconnecttime > 19:
                    break
        self.shutdown_flag = threading.Event()
        self.shutdown_flag.set()
        self.sock.setblocking(True)
        return notconnect

    def disconnect(self):
        
        self.shutdown_flag.clear()
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.logger.info('Data server disconnected')

        return
    
    def readData(self, startPoint, endPoint):
        if 0 <= startPoint < endPoint <= self.getMessageQueueSize():
            # 如果消息队列中有足够的数据，就读取数据
            tmp = []
            self.lock.acquire()
            for i in range(startPoint, endPoint):
                tmp.append(self.messageQueue[i])
            self.lock.release()

            return tmp

        else:
            # 否则等待数据继续添加
            return None


    def getMessageQueueSize(self):
        self.lock.acquire()
        queue_len = len(self.messageQueue)
        self.lock.release()
        return queue_len
    
    #old read Fixed Data
    
    def readFixedData(self, startPoint, length):
        
        # 降采样之前
        srate = self.record_srate
        startPoint, realLEN = int(startPoint*srate), int(length*srate)
        realLEN = startPoint+realLEN

        self.downRatio = int(self.srate*length)

        while len(self.eventPoint) != 0:
            events = self.eventPoint.pop()
            if self.keepEvent == False:
                point, packageINX = events
            else:
                point,packageINX,eventType,sp = events

            # 要读多少个数据包
            pacNUM = math.ceil((realLEN+startPoint)/self.packetSize)

            data = None
            while data is None:
                data = self.readData(packageINX+1, packageINX+pacNUM+1+1)

            data = np.hstack(data)

            # f,ax = plt.subplots()
            # ax1 = ax.twinx()
            # ax1.plot(data[0],color='black')
            # ax.plot(data[1],color='red')
            data = data[:, (startPoint+point):(startPoint+point+realLEN)]
            # self.eventExist = False

            data = data[:-1, :]

            data = self.preprocess(data)
            if self.keepEvent == False:
                return data, None  
            else:
                return data, eventType
        else:
            return None, None
    
    
    def readFlowData(self, startPoint, length):
        # 降采样之前
        # realLen = int(4*length)
        srate = self.record_srate
        startPoint, realLen = int(startPoint*srate), int(length*srate)
        realLen = startPoint+realLen
        
        self.downRatio = int(self.srate*length)

        while self.eventExist is True:
            
            self.eventPoint = [self.eventPoint[-1]]
            events = self.eventPoint[0]
            point, packageInx, eventType, sp = events

            # 要读多少个数据包
            pacNUM = math.ceil((realLen+startPoint)/self.packetSize)

            data = None
            while data is None:
                data = self.readData(packageInx+1, packageInx+pacNUM+1+1)

            data = np.hstack(data)
            data = data[:, (startPoint+point):(startPoint+point+realLen)]

            data = data[:-1, :]


            data = self.preprocess(data)


            return data, eventType
        else:
            return None, None

    # new
    def _findEvent(self,data):

        events = data[-1,:].flatten()

        if np.any(events != 0) and max(events)<50:
            # event 从哪个数据包开始
            packageInx  =  self.getMessageQueueSize()-1
            # 在该数据包的哪个位置
            point = int(np.argwhere(events))

            self.eventPoint.append([point,packageInx])
            self.packetSize = data.shape[-1]
            self.eventExist =True
            print('Received Event,ready to start processing')
            return self
        
    def preprocess(self,x):
        from scipy.signal import resample

        x = resample(x,self.downRatio,axis=-1)  # 降采样至1/4

        notchFilter, bpFilter = self.filters

        b_notch, a_notch = notchFilter
        # b_bp, a_bp = bpFilter

        x_notched = signal.filtfilt(b_notch, a_notch, x, axis=-1)
        # x_filtered = signal.filtfilt(b_bp, a_bp, x_notched, axis=-1)

        # processed = x_filtered - np.mean(x_filtered,axis=-1,keepdims=True)

        processed = x_notched

        return processed

    def _initFilter(self):

        # notch
        fs = self.srate  # Sample frequency (Hz)
        f0 = 50.0  # Frequency to be removed from signal (Hz)
        Q = 30.0  # Quality factor

        b, a = signal.iirnotch(f0, Q, fs)
        notch = [b, a]

        # band pass
        b, a = signal.butter(N=5, Wn=90, fs=fs, btype='lowpass')
        bp = [b, a]

        return notch, bp


    def clientProcess(self,sock):
        # receive head
        # head size will always be 20

        headSize = 20
        head = sock.recv(headSize)
        head = np.frombuffer(head,dtype=np.uint8)

        # receive body if header meets request
        message = self._parseHeader(head)

        data = sock.recv(message['packetSize'],socket.MSG_WAITALL)
        data = np.frombuffer(data,dtype=np.uint8)

        return message,data

    def _parseHeader(self,head):
        # parsing head

        code = np.flip(head[4:6]).copy().view(dtype=np.uint16)
        request = np.flip(head[6:8]).copy().view(np.uint16)
        startSample = np.flip(head[8:12]).copy().view(np.uint32)
        packetSize = np.flip(head[12:16]).copy().view(np.uint32)

        message = {
            'code':code,
            'request':request,
            'startSample':startSample[0],
            'packetSize':packetSize[0]
        }

        return message

    def requestInfo(self):

        # 获得设置信息

        sendBasicInfo = NeuroScanMessage().getBasicInfo()

        self.sock.send(sendBasicInfo)

        message,data = self.clientProcess(self.sock)

        size = np.uint8(data[0:4]).copy().view(dtype=np.uint32)
        eegChan = np.uint8(data[4:8]).copy().view(np.uint32)
        sampleRate = np.uint8(data[8:12]).copy().view(np.uint32)
        datasize = np.uint8(data[12:16]).copy().view(np.uint32)

        info = {
            'size':size,
            'eegChan':int(eegChan),
            'sampleRate':sampleRate,
            'datasize':datasize[0]
        }

        self.info = info
        return self

    def requestEEG(self,socket):

        # 这只是一个指令
        sendStartStreaming = NeuroScanMessage().startStreaming()
        # 还需要端口发送
        self.sock.send(sendStartStreaming)

        message,data = self.clientProcess(socket)

        if message['code'] ==2:
            # eeg data
            receiveSamples = len(data)/self.info['datasize']*self.info['eegChan']
            # unpack data will be transformd to chan*samples format
            data = self._unpackEEG(data)

            self.package = dict(
                data = data,
                startSample = message['startSample'],
            )

        elif message['code'] ==3:
            # event
            eventType = data[0:4].copy().view(dtype=np.uint32)
            startEvent = data[8:12].copy().view(dtype=np.uint32)

            self.event = dict(
                eventType = eventType,
                startEvent = startEvent
            )

        elif message['code'] == 1:
            # 阻抗
            pass

        return self

    def _addEvent(self):

        if self.package is None :
            return None

        packet = self.package['data']
        startData = self.package['startSample']

        length = packet.shape[-1]
        events = np.zeros((1,length),dtype=np.single)


        if self.event is not None:

            eventType = self.event['eventType']

            if eventType <200:

                startEvent = self.event['startEvent']
                events[:,startEvent-startData] = eventType

                # print('Add event {type} to data package,start at {t}'.format(
                #     type=eventType, t=startEvent))

                self.package['eventType'] = None

                packageINX  =  self.getMessageQueueSize()-1
                point = int(np.argwhere(events[0]))

                if self.keepEvent == False:
                    elist = [point, packageINX]
                else:
                    elist = [point, packageINX,eventType,startEvent]

                self.eventPoint.append(elist)
                self.event = None
                self.eventExist = True

                # self.messageQueue.pop()
        events[0,events[0]==0] = 1
        wholePacket = np.concatenate((packet,events),axis=0)

        return wholePacket,startData

    def _unpackEEG(self,data):

        if self.info['datasize'] == 2:
            data = data.view(np.int16)
        elif self.info['datasize'] == 4:
            packect = data.view(np.single)

        numSamples = int(len(packect)/self.info['eegChan'])
        packect = np.reshape(packect,(self.info['eegChan'],numSamples),order='F')

        # 放缩系数
        packect = packect/1e6

        return packect


    def requestChannelInfo(self):

        # 获得设置信息
        offset_channelId    =                     1
        offset_chanLabel    = offset_channelId  + 4
        offset_chanType     = offset_chanLabel  + 80
        offset_deviceType   = offset_chanType   + 4
        offset_eegGroup     = offset_deviceType + 4
        offset_posX         = offset_eegGroup   + 4
        offset_posY         = offset_posX       + 8
        offset_posZ         = offset_posY       + 8
        offset_posStatus    = offset_posZ       + 8
        offset_bipolarRef   = offset_posStatus  + 4
        offset_addScale     = offset_bipolarRef + 4
        offset_isDropDown   = offset_addScale   + 4
        offset_isNoFilter   = offset_isDropDown + 4


        # Raw length
        chanInfoLen = (offset_isNoFilter + 4) - 1
        # Length of CURRY channel info struct in bytes, consider padding
        chanInfoLen = round(chanInfoLen/8)*8

        channelNUM = self.info['eegChan']

        sendChannelInfo = NeuroScanMessage().getChannelInfo()
        self.sock.send(sendChannelInfo)

        message,data = self.clientProcess(self.sock)

        channelLabels = []
        for i in range(channelNUM):
            j = chanInfoLen*i

            label = data[j+offset_chanLabel-1:j+(offset_chanType-1)]
            label = label[:6].tolist()
            label = ''.join([chr(item) for item in label ])
            label = label.replace('\x00','')

            channelLabels.append(label)

        self.info['channels'] = channelLabels

        channelLabels = [' %s' % label for label in channelLabels]
        channelLabels = ''.join(channelLabels)
        print('Send Data from: %s'%channelLabels)

        return self