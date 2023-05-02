import os

# get current directory
current_path  = os.getcwd()
# relative path to add
relative_path = "OperationSystem"

# join paths to get full path
full_path = os.path.join(current_path, relative_path)

# add the path to the system paths
import sys
sys.path.append(full_path)

from AnalysisProcess.BasicAnalysisProcess import BasicAnalysisProcess
import numpy as np
import pickle
import pandas as pd
import os
# from PyQt5.QtWidgets import QMessageBox
import time
from AnalysisProcess.OperatorMethod.spatialFilter import fbCCA
from datetime import datetime


class TestingProcess(BasicAnalysisProcess):
    def __init__(self) -> None:
        super().__init__()


    def initial(self, controller=None, config=None, streaming=None, messenger=None,progress_manager = None):

        super().initial(controller, config, streaming, messenger,progress_manager)

        # modelname = os.path.join(self.savepath, 'models/%sModel.pkl'%self.paradigm)
        modelname = os.path.join(self.savepath, f'models/{self.prefix}Model.pkl')

        if config.MODE == "TRAIN": # training mode, train new model.
            pass 
        
        elif config.MODE =="TEST" or config.MODE =="USE" or config.MODE =="DEBUG":
        
            if os.path.exists(modelname) or config.feature_algo == "FBCCA":
                
                self.loadModel(modelname, config.feature_algo)
                
                self.controller.trainFlag=True
                    
            else: # model not exists
                
                path = os.path.join(self.savepath, 'data')
                suffix = 'train.pkl'
                _prefix = self.prefix
                method_name = f'{self.feature_algo}_'
                prefix = _prefix.replace(method_name, "")
                
                # List all files in the specified directory
                all_files = os.listdir(path)
                
                # Filter the files based on the prefix and suffix
                matching_files = [file for file in all_files if file.endswith(suffix) and file.startswith(prefix)]


                if matching_files:
                    
                    self.algorithm = self.reTrainModel(matching_files)
                    # with open(os.path.join(self.savepath, 'models/%sModel.pkl' % self.paradigm), "wb+") as fp:
                    with open(modelname, "wb+") as fp:
                        pickle.dump(self.algorithm, fp,protocol=pickle.HIGHEST_PROTOCOL)
                    self.controller.trainFlag = True
                    
                else:
                    
                    # Create the error dialog
                    print("\n\nCaution")
                    print("No previous data and model found, will train the model first\n\n")
                    self.totalTargetNUM = 3
                    pass
                
            
            
        # 用来保存模型表现：ITR,accuracy
        self.scores = []
        # 用来保存每个trial的结果
        self.frames= []

        return

    def reTrainModel(self,files):
        # train
        trainX = None
        trainy = None

        for filename in files:
            path = os.path.join(self.savepath, 'data', filename)
            
            with open(path, "rb") as fp:
                data = pickle.load(fp)

            if trainX is None:
                trainX = np.squeeze(data['X'])
                trainy = np.squeeze(data['y'])
            else:
                trainX = np.concatenate((trainX, data['X']), axis=0)
                trainy = np.concatenate((trainy, data['y']), axis=0)
        
        
        # from AnalysisProcess.OperatorMethod.spatialFilter import TDCA
        # model = TDCA(winLEN=self.winLEN, srate=self.srate,lag=self.lag)
        if self.feature_algo =='TRCA':
            from AnalysisProcess.OperatorMethod.spatialFilter import TRCA
            model = TRCA(montage = self.targetNUM, winLEN=self.winLEN, srate=self.srate, sync_mode = self.sync_mode,p_value = self.p_value,
                        frequency = self.frequency, phase = self.phase, n_band=5)
            
        elif  self.feature_algo == "FBCCA":
            from AnalysisProcess.OperatorMethod.spatialFilter import fbCCA
            model = fbCCA(frequency = self.frequency, winLEN=self.winLEN, srate=self.srate,conditionNUM = self.targetNUM, lag = self.lag)
        elif self.feature_algo == "TDCA":
            from AnalysisProcess.OperatorMethod.spatialFilter import TDCA
            model = TDCA(winLEN=self.winLEN,srate=self.srate)
            
        
        model.fit(trainX, trainy)

        return model


    def loadModel(self,modelname, feature_algo = None):
        
        
        if feature_algo != "FBCCA":
            with open(modelname,"rb") as fp:
                self.algorithm = pickle.load(fp)
        else:
            
            model = fbCCA(frequency = self.frequency, winLEN=self.winLEN, srate=self.srate,conditionNUM = self.targetNUM, lag = self.lag)
            model.fit(None, model.montage+1)
            self.algorithm = model
            
        self.algorithm.sync_mode = self.sync_mode
        self.algorithm.p_value = self.p_value
        pass

    def run(self):

        # 同步系统,包含event
        
        if self.sync_mode == "Normal":
            # 同步系統
            window_time = self.winLEN
            while True:
                epoch, event = self.streaming.readFixedData(0, window_time+self.lag)
                time.sleep(0.04)
                if epoch is not None:
                    self.streaming.eventExist = False
                    break
                if self.messenger.state.control_state == 'EXIT': break
            
            
            # 计算结果
            if self.messenger.state.control_state != 'EXIT':
                result = self.getResult(epoch)
            else:
                result = None
        elif self.sync_mode =="NP":
            window_time = self.winLEN
            # 伪异步系統
            while True:
                while True:
                    epoch, event = self.streaming.readFlowData(0, window_time+self.lag)
                    time.sleep(0.01)
                    if epoch is not None:
                        break
                    if self.messenger.state.control_state == 'EXIT': break
                
                # 计算结果
                if self.messenger.state.control_state != 'EXIT':
                    result = self.getResult(epoch)
                else:
                    result = None
                    break
                    
                if result is not None: 
                    break
                elif window_time == self.winLEN:
                    result = -1
                    break
            
        else:
            # window_time = self.winLEN/4 - self.winLEN/8 
            window_time = 0.35 - self.winLEN/8
            # 伪异步系統
            while True:
                window_time += self.winLEN/8 # multiple of winLEN
                if window_time >= self.winLEN: 
                    window_time = self.winLEN
                
                while True:
                    epoch, event = self.streaming.readFlowData(0, window_time+self.lag)
                    time.sleep(0.01)
                    if epoch is not None:
                        break
                    if self.messenger.state.control_state == 'EXIT': break
                
                # 计算结果
                if self.messenger.state.control_state != 'EXIT':
                    result = self.getResult(epoch)
                else:
                    result = None
                    break
                    
                if result is not None: 
                    break
                elif window_time == self.winLEN:
                    result = -1
                    break
        
        
        if result != -1:
            
            self.streaming.eventExist = False
            
                
                
            if self.messenger.state.control_state == 'EXIT': # DO last time reporting
                print('Exiting operation process...')
                
                
                
                
                _file_name = f'{self.prefix_with_time}test.pkl'
                method_name = f'{self.feature_algo}_'
                file_name = _file_name.replace(method_name, "")
                file_path = os.path.join(self.savepath,'data',file_name)
                
                with open(file_path, "wb+") as fp:
                    pickle.dump(self.controller.testData, fp,
                                protocol=pickle.HIGHEST_PROTOCOL)

                self.peroformance()
                # self.performance_accross_winlen()
            else:
                # 汇报结果
                self.controller.report(result)

                self.logger.success('Reported No.%s epoch,True event %s identified as %s'%(self.controller.currentEpochINX,event,result))
                
                # # Save checkpoint
                # checkpoint = {
                #     'epoch': epoch,
                #     'event': event,
                #     'result': result,
                #     'window_time': window_time,
                #     'currentEpochINX': self.controller.currentEpochINX,
                #     'currentBlockINX': self.controller.currentBlockINX,
                #     'testData': self.controller.testData,
                #     'results': self.controller.results,
                #     'prefix_with_time': self.prefix_with_time,
                #     'feature_algo': self.feature_algo,
                #     'savepath': self.savepath,
                #     'frames': self.frames,
                #     'scores': self.scores
                # }

                # checkpoint_file = f'{self.prefix_with_time}_checkpoint.pkl'
                # with open(checkpoint_file, 'wb') as f:
                #     pickle.dump(checkpoint, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                self._collectTest(epoch,event,result,window_time)

                self.controller.current_process = self.controller.wait_process
                self.messenger.state.current_detect_state = 'INIT'
                

        return

    def _collectTest(self,x,y,result,window_time):

        epochINX = self.controller.currentEpochINX
        blockINX = self.controller.currentBlockINX
        cueThisBlock = len(self.cueEvents[blockINX])

        # X: epoch * chn * T
        self.controller.testData['X'].append(x[np.newaxis,:,:])
        self.controller.testData['y'].append(y)
        self.controller.testData['t'].append(window_time)
        
        # 保存结果
        self.controller.results.append(result)

        if (epochINX+1) % cueThisBlock == 0:

            self.controller.currentBlockINX += 1
            
            
            
            
            if self.MODE == "USE":
                _file_name = f'{self.prefix_with_time}use.pkl'
            else: # including DEBUG mode
                _file_name = f'{self.prefix_with_time}test.pkl'
                
            method_name = f'{self.feature_algo}_'
            file_name = _file_name.replace(method_name, "")
            file_path = os.path.join(self.savepath,'data',file_name)
            
            with open(file_path, "wb+") as fp:
                pickle.dump(self.controller.testData, fp,
                            protocol=pickle.HIGHEST_PROTOCOL)
                
            if self.MODE != 'USE':
                self.peroformance()
                # self.performance_accross_winlen()
            else:
                self.controller.currentBlockINX = 0 # never ending run
                
            # if self.MODE == "DEBUG":
            self.controller.currentEpochINX = -1
            # return
            
        # USE mode special, record all the epoch
        if self.MODE == "USE":
            self.note_down()
            
        self.controller.currentEpochINX += 1
        

        return


    def peroformance(self):

        from sklearn.metrics import accuracy_score
        from OperationSystem.AnalysisProcess.OperatorMethod.utils import ITR
        
        
        # 按照block为节奏记录结果

        blockINX  = self.controller.currentBlockINX
        y = np.concatenate(self.controller.testData['y'][-(self.controller.currentEpochINX+1):])
        y_ = self.controller.results[-(self.controller.currentEpochINX+1):]
        winLEN = np.array(self.controller.testData['t'][-(self.controller.currentEpochINX+1):])
        average_winLEN = np.mean(winLEN)
        
        # 记录本block测试结果
        r = pd.DataFrame({
            'epochINX':np.arange(1,self.controller.currentEpochINX+2),
            'event':y,
            'eventChar':[self.config.char[self.config.events.index(i)] for i in y],
            'result':y_,
            'resultChar': [self.config.char[self.config.events.index(i)] for i in y_],
            'winLEN': winLEN
        })
        r['blockINX'] = blockINX
        r['subject'] = self.personName
        # r['winLEN'] = self.winLEN
        # r['winLEN'] = winLEN
        r['ISI'] = self.config.ISI
        r['paradigm'] = self.paradigm


        self.frames.append(r)
        # self.frames = r
        df = pd.concat(self.frames, axis=0, ignore_index=True)
        
        
        file_name = f'{self.prefix_with_time}trackEpoch.csv'
        file_path = os.path.join(self.savepath,'record',file_name)
        
        df.to_csv(file_path, mode='w', header=True)
        
        
        # 本block结果评估
        accuracy = accuracy_score(y,y_)
        itr = ITR(self.targetNUM, accuracy, average_winLEN)

        # Create the new DataFrame with the current block's results
        f = pd.DataFrame({
            'accuracy': [accuracy],
            'itr': [itr],
            'winLEN': [average_winLEN],
            'subject': [self.personName],
            'block': [blockINX],
            'paradigm': [self.paradigm],
            'datetime': [datetime.now().strftime('%Y%m%d%H%M%S')]
        })
        self.scores.append(f)

        # Prepare to save the data
        file_name = f'{self.prefix}online.csv'
        file_path = os.path.join(self.savepath, 'record', file_name)
        file_exists = os.path.exists(file_path)

        # Save the data to the CSV file
        if file_exists:
            f.to_csv(file_path, mode='a', header=False, index=False)
        else:
            f.to_csv(file_path, mode='w', header=True, index=False)

        
        self.logger.success('Finished No.{} test block, accuracy: {:.2%}, ITR: {:.2f}'.format(blockINX, accuracy, itr))


        return
    
    def note_down(self):
        # 按照block为节奏记录结果
        y_ = self.controller.results[-1]
        winLEN = np.array(self.controller.testData['t'][-1])

        # 记录本block测试结果
        r = pd.DataFrame({
            'epochINX': np.arange(1, self.controller.currentEpochINX + 2),
            'result': y_,
            'resultChar': self.config.char[self.config.events.index(y_)],
            'winLEN': winLEN
        })
        r['subject'] = self.personName
        r['ISI'] = self.config.ISI
        r['paradigm'] = self.paradigm

        self.frames.append(r)
        
        df = pd.concat(self.frames, axis=0, ignore_index=True)


        file_name = f'{self.prefix_with_time}trackEpoch_use.csv'
        file_path = os.path.join(self.savepath, 'record', file_name)

        df.to_csv(file_path, mode='w', header=True)
        
        return
