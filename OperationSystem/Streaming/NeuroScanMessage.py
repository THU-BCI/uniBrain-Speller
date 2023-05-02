import numpy as np


class  NeuroScanMessage():
    def __init__(self) -> None:
        # 初始化，定义各种请求类型
        self.initial()


    def initial(self):
        # infoType
        self.dataType = dict(
            InfoType_Version = 1,
            InfoType_BasicInfo = 2,
            InfoType_ChannelInfo = 4
        )
        # dataType
        self.dataType = dict(
            Data_Info = 1,
            Data_Eeg = 2,
            Data_Event = 3,
            Data_Impedance = 4

        )
        # blockType
        self.blockType = dict(
            DataTypeFloat32bit = 1,
            DataTypeEventList = 2
        )
        # requestType
        self.requestType = dict(
            RequestVersion = 1,
            RequestChannelInfo = 3,
            RequestBasicInfoAcq = 6,
            RequestStreamingStart = 8,
            RequestStreamingStop = 9
        )
        # controlCode
        self.controlType = dict(
            CTRL_FromServer = 1,
            CTRL_FromClient = 2,
        )

        return self

    def _convertMessage(self,charID,code,request,samples,sizeBody,sizeUn):
        # 格式化
        self.charID = np.fromstring(charID,dtype='uint8')
        self.code = np.uint16([code])
        self.request = np.uint16([request])
        self.samples = np.uint32([samples])
        self.sizeBody = np.uint32([sizeBody])
        self.sizeUn = np.uint32([sizeUn])

        return self


    def initHeader(self,charID,code,request,samples,sizeBody,sizeUn):

        self._convertMessage(charID,code,request,samples,sizeBody,sizeUn)
        # char 
        charFlow = self.charID
        # code
        codeflow = self.code.byteswap().view(np.uint8)
        # request
        requestFlow = self.request.byteswap().view(np.uint8)
        # samples
        samples = self.samples .byteswap().view(np.uint8)
        # sizeBody
        sizeBody = self.sizeBody.byteswap().view(np.uint8)
        # sizeUn
        sizeUn = self.sizeUn.byteswap().view(np.uint8)

        flow = np.concatenate((charFlow,codeflow,requestFlow,samples,sizeBody,sizeUn))

        return flow

    def startStreaming(self):

        # start sending data

        header = self.initHeader(
            charID='CTRL',
            code=self.controlType['CTRL_FromClient'],
            request=self.requestType['RequestStreamingStart'],
            samples=0,sizeBody=0,sizeUn=0
        )

        return header

    def getChannelInfo(self):

        header = self.initHeader(
            charID='CTRL',
            code=self.controlType['CTRL_FromClient'],
            request=self.requestType['RequestChannelInfo'],
            samples=0,sizeBody=0,sizeUn=0
        )


        return header

    def getBasicInfo(self):

        header = self.initHeader(
            charID='CTRL',
            code=self.controlType['CTRL_FromClient'],
            request=self.requestType['RequestBasicInfoAcq'],
            samples=0,sizeBody=0,sizeUn=0
        )


        return header


