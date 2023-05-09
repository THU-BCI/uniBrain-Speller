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
        
        
        # Initialize algorithm: fbcca or trca
        self.feature_algo = config.feature_algo
        self.targetNUM = config.targetNUM
        # Total trial count
        self.totalTargetNUM = config.blockNUM * config.targetNUM
        
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
        self.prefix_with_time = config.prefix_with_time
        self.progress_manager = progress_manager
        
        

    def prepareFolder(self):
        """
        Prepare the folder structure for saving results.
        """
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
        """
        Run the analysis process.
        """
        pass


    @abstractmethod
    def getResult(self,data):
        """
        Get the result from the analysis process.
        """
        result = self.algorithm.predict(data, self.p_value, self.sync_mode)
        return result[0]

