import os
from abc import abstractmethod
import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm
from datetime import datetime
import pickle



class BasicAnalysisProcess:
    def __init__(self) -> None:
        pass


    @abstractmethod
    def initial(self, controller=None, config=None, streaming=None, messenger=None, progress_manager=None):

        # 3 essentials: controller, config, and data streaming client
        self.controller = controller
        self.config = config
        self.streaming = streaming
        self.messenger = messenger
        self.logger = logger
        
        
        # 初始化算法：fbcca
        self.feature_algo = config.feature_algo
        self.targetNUM = config.targetNUM
        # 训练 trial 数目
        self.totalTargetNUM = config.blockNUM * config.targetNUM
        # # 测试 trial 数目
        # self.totalTargetNUM = config.blockNum * config.targetNUM
        self.winLEN = config.winLEN
        self.srate = config.srate
        self.personName = config.personName
        self.paradigm = config.paradigm
        self.resultPath = config.resultPath 
        self.prepareFolder()

        self.displayChar = config.displayChar
        self.cueEvents = config.cueEvents
        self.lag = config.lag
        self.n_band = config.n_band
        
        #new
        self.MODE = config.MODE
        self.sync_mode = config.sync_mode
        self.p_value = config.p_value
        self.frequency = config.frequency
        self.phase = config.phase
        
        
        self.prefix = config.prefix
        
        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # self.prefix_with_time = f"{self.prefix}{current_time}_"
        self.prefix_with_time = config.prefix_with_time
        self.progress_manager = progress_manager
        

    def prepareFolder(self):
        fatherAdd = self.resultPath
        sonAdd = os.path.join(fatherAdd,self.personName)
        if not os.path.exists(sonAdd):
            os.makedirs(os.path.join(sonAdd, 'images'))
            os.makedirs(os.path.join(sonAdd, 'models'))
            os.makedirs(os.path.join(sonAdd, 'data'))
            os.makedirs(os.path.join(sonAdd, 'record'))
            os.makedirs(os.path.join(sonAdd, 'report'))
        self.savepath = sonAdd
        return


    @abstractmethod
    def run(self):

        pass


    @abstractmethod
    def getResult(self,data):
        
        
        # DEBUG
        # Save variables needed for TRCA model
        # variables = {'data': data}
        # checkpoint_path = "checkpoint_basicAnalysisProcess.pkl"
        # with open(checkpoint_path, "wb+") as fp:
        #     pickle.dump(variables, fp, protocol=pickle.HIGHEST_PROTOCOL)
            
        result = self.algorithm.predict(data, self.p_value, self.sync_mode)
        return result[0]

