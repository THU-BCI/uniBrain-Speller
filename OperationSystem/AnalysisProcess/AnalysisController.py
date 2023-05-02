
# DEBUG use
import sys
# Append the current directory to the system path
sys.path.append('.')


from OperationSystem.AnalysisProcess.TestingProcess import TestingProcess
from OperationSystem.AnalysisProcess.WaitAnalysisProcess import WaitAnalysisProcess
from OperationSystem.AnalysisProcess.TrainingProcess import TrainingProcess
import pandas as pd
import pickle
import numpy as np
import datetime
import os

class AnalysisController:
    def __init__(self):
        self.current_process = None
        self.algorithm = None

        self.currentBlockINX=0
        self.currentEpochINX = 0

        # 等待训练结束后会改变Flag
        self.trainFlag = False

    def initial(self, config, streaming,messenger,progress_manager=None):

        self.messenger = messenger

        # 个人数据
        self.trainData = dict(
            X = [],# data
            y = [], # label
        )
        self.testData = dict(
            X=[],  # data
            y=[],  # label
            t = [], # time window
        )

        self.results = []

        # 测试阶段
        self.testing_process = TestingProcess()
        self.testing_process.initial(self, config, streaming, messenger,progress_manager)
        

        # 训练阶段
        self.training_process = TrainingProcess()
        self.training_process.initial(self, config, streaming, messenger,progress_manager)

        # 等待下一次处理
        self.wait_process = WaitAnalysisProcess()
        self.wait_process.initial(self, config, streaming, messenger)

        self.current_process = self.wait_process

        return self

    def report(self, resultID):
        message = 'RSLT:'+str(int(resultID))
        self.messenger.send_exchange_message(message)


    def run(self):
        # algorithm需要在各个状态之间传递
        self.current_process.run()



# debug use
if __name__ == "__main__":
    
    
    # Define the path to the checkpoint file
    checkpoint_path = "CommonSystem\\config.pkl"
    sys.path.append('.GraphicUserInterface')
    import GraphicUserInterface.ui_keyboard
    
    # Load variables saved in pickle
    with open(checkpoint_path, "rb") as fp:
        config = pickle.load(fp)
    
    prc = TestingProcess()
    
    from loguru import logger
    prc.logger = logger
    class Controller:
        def __init__(self):
            self.trainData = {
                'X': None,
                'y': None
            }
            self.training_process = None
    prc.controller = Controller()
    
    prc.controller.training_process = TrainingProcess()
    # Update variables with saved variables
    prc.targetNUM = config.targetNUM
    # prc.targetNUM = config.targetNUM
    prc.winLEN = config.winLEN
    prc.srate = config.srate
    prc.frequency = config.frequency
    prc.phase = config.phase
    prc.lag = config.lag
    prc.n_band = config.n_band
    prc.cueEvents = config.cueEvents
    prc.MODE = config.MODE
    prc.prefix_with_time = "ssvep_Mouse 13 keys_TRCA_20230407_153251_"
    prc.config = config
    prc.personName = config.personName
    prc.paradigm = config.paradigm
    prc.prefix = config.prefix
    
        
        
    prc.feature_algo = "TRCA"
    
    
    checkpoint_file = f'{prc.prefix_with_time}_checkpoint.pkl'
    with open(checkpoint_file, 'rb') as f:
        loaded_checkpoint = pickle.load(f)

    # Restore variables
    epoch = loaded_checkpoint['epoch']
    event = loaded_checkpoint['event']
    result = loaded_checkpoint['result']
    window_time = loaded_checkpoint['window_time']
    prc.controller.currentEpochINX = loaded_checkpoint['currentEpochINX']
    prc.controller.currentBlockINX = loaded_checkpoint['currentBlockINX']
    prc.controller.testData = loaded_checkpoint['testData']
    prc.controller.results = loaded_checkpoint['results']
    prc.prefix_with_time = loaded_checkpoint['prefix_with_time']
    prc.feature_algo = loaded_checkpoint['feature_algo']
    prc.savepath = loaded_checkpoint['savepath']
    
    
    
    # DEBUG's DEBUG
    prc.frames = []
    prc.scores = []
    # prc.frames = loaded_checkpoint['frames']
    # prc.scores = loaded_checkpoint['scores']
    
    prc._collectTest(epoch,event,result,window_time)