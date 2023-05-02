import numpy as np
import string
import os
import pickle

class Config():
    """Configuration class to store settings and information for the experiment."""
    
    def __init__(self) -> None:
        """Initialize the Config object with default values."""
        self.default_config()


    def default_config(self,):
        """Reset configuration settings to their default values."""
        self.display_info()
        self.subject_info()
        self.experiment_info()
        self.connect_info()


    def subject_info(self, personName='joedoe', age='unknown', gender='m/f'):
        """Set subject information for the experiment, such as name, age, and gender."""
        self.personName = personName
        self.age = age
        self.gender = gender


    def display_info(self,  imageAddress = 'StimulationSystem/test_pics/', refreshRate=60, stiLEN=3, resolution=(1920, 1080), 
                    layout=(5, 8), cubicSize=140, interval=50, trim=(225, 90), 
                    phase=[i* np.pi for i in [0, 0.35, 0.70, 1.05, 1.40,1.75, 0.1, 0.45, 0.80, 1.15,1.50, 1.85, 0.20, 0.55, 0.9, 1.25, 1.60, 1.95, 0.30, 0.65, 1.0, 1.35, 1.70, 0.05, 0.40, 0.75, 1.10, 1.45, 1.80, 0.15, 0.50, 0.85, 1.20, 1.55, 1.90, 0.25, 0.60, 0.95, 1.30, 1.65]], frequency=np.linspace(8.0, 15.8, 40), 
                    char=list(string.ascii_lowercase) + list(np.arange(10))+['.', ' ', ',', '?'],paradigm='ssvep',
                    cueTime = 2, windowIndex = 0, acquisitionSys = 'NeuroScan',maxFrames = 180,
                    halfScreen = False, halfScreenPos = 0):
        """Set display information for the experiment, such as image paths, refresh rates, and screen resolution."""
        self.paradigm  = paradigm
        self.refreshRate = refreshRate
        self.stiLEN = stiLEN
        x_resolution , y_resolution = resolution
        self.resolution = (x_resolution , y_resolution)
        self.layout = layout
        self.cubicSize = cubicSize
        self.interval = interval
        self.trim = trim
        # char 需要转换为按照列排列的顺序
        self.char = np.reshape(char,layout[::-1],order='F').flatten().tolist()
        self.cueTime = cueTime
        self.maxFrames = maxFrames
        
        self.frequency = frequency
        self.phase = phase
        self.addSTI = imageAddress +os.sep +paradigm
        self.windowIndex = windowIndex
        
        self.acquisitionSys = acquisitionSys
        
        self.halfScreen = halfScreen
        self.halfScreenPos = halfScreenPos
        

    def experiment_info(self, MODE= None, key_list = None, targetNUM=40, blockNum = 6, srate=250, winLEN=1,lag=0.14, keyType="Mouse 13 keys",chnMontage = "Quick-Cap 64",
                n_band=5,chnNUM=64, paradigm='ssvep', resultPath='outFolder', texts='random',ISI=0.5, feature_algo="TRCA", sync_mode = "Normal", p_value = 0.01):
        """Set experiment information and parameters, such as the mode, target and block numbers, and data processing settings."""
        
        if MODE == "DEBUG":# free spelling!!
            texts = [
                    "⇧A ZEBRA, 2 MICE, 5 DOGS JUMPED.↵",
                    "3 KIND CATS, 6 FROGS, 9 FISH SWIM.↵",
                    "⇧QUIETLY, 8 ELEPHANTS WALK BY 4 TREES.↵",
                    "⇧VEXING BUGS ON 1 LEAF, 0 HARM DONE.↵",
                    "7 HENS LAY GOLDEN EGGS, X MARKS SPOT.↵",
                    "⇧WHY DID UPTON, THE 1ST, BUY 9←8 PLUMS⇧/↵",
                ]
        
        # must be the last one called!!
        self.paradigm = paradigm
        self.resultPath = resultPath
        self.targetNUM = targetNUM
        
        if MODE != "DEBUG":
            self.blockNUM = blockNum
        else:
            self.blockNUM = len(texts)
            
        self.srate = srate
        self.lag = lag
        self.winLEN = winLEN
        self.n_band = n_band
        self.chnNUM = chnNUM
        self.ISI = ISI
        self.feature_algo = feature_algo
        self.MODE= MODE
        self.sync_mode = sync_mode
        self.p_value = p_value
        self.chnMontage = chnMontage
        self.key_list = key_list
        
        if self.MODE != None:
            self.frequency = [key.frequency for key in self.key_list.keys]
            self.phase = [key.phase for key in self.key_list.keys]
            self.char = [key.key_name for key in self.key_list.keys]
        
        self.project_cue(texts)
        self.keyType = keyType
        
        if self.key_list != None:
            self.prefix = f"{self.paradigm}_{keyType}_{self.feature_algo}_"
            from datetime import datetime
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.prefix_with_time = f"{self.prefix}{current_time}_"
            

    def connect_info(self, COM='5EFC', streaming_ip='192.168.1.13', streaming_port=4455, record_srate=1000, host_ip='192.168.1.92', host_port=11000):
        """Set connection information for the experiment, such as communication ports and IP addresses."""
        self.COM = COM
        self.streaming_ip = streaming_ip
        self.streaming_port = streaming_port
        self.record_srate = record_srate

        self.host_ip = host_ip
        self.host_port = host_port


    def optimized_info(self,optWIN=1,optBlockNUM=5,classNUM=160,seedNUM=1000):
        """Set optimization information for the experiment, such as window size, block number, and class number."""        
        self.optWIN = optWIN
        self.optBlockNUM = optBlockNUM
        self.classNUM = classNUM
        self.seedNUM = seedNUM

    def project_cue(self, texts):
        """Set the cue events, indices, and display characters based on the input texts and the experiment mode."""
        self.events = np.arange(1,self.targetNUM+1,1).tolist()

        if self.MODE == "DEBUG":
            
            self.cueEvents = [[self.events[self.char.index(s)] for s in text] for text in texts]
            self.cueIndices = [[self.char.index(s) for s in text] for text in texts]
            self.displayChar = texts


        elif self.MODE == "USE":
            
            # cueIndice = np.zeros(5, dtype=int)  
            cueIndice = np.full(5, 0)
            cueEvents = [self.events[i] for i in cueIndice]
            cueChars = ['%s' % self.char[i] for i in cueIndice]
            self.cueEvents = np.tile(cueEvents, (1, 1)).tolist()
            self.cueIndices = np.tile(cueIndice, (1, 1)).tolist()
            self.displayChar = np.tile(cueChars, (1, 1)).tolist()
            
        else:
            
            cueIndice = np.arange(0,self.targetNUM,1)
            cueEvents = [self.events[i] for i in cueIndice]
            cueChars = ['%s' % self.char[i] for i in cueIndice]
            self.cueEvents = np.tile(cueEvents, (self.blockNUM, 1)).tolist()
            self.cueIndices = np.tile(cueIndice, (self.blockNUM, 1)).tolist()
            self.displayChar = np.tile(cueChars, (self.blockNUM, 1)).tolist()

        return
    

def config_make_file(win):
    """Create a configuration file for the experiment using the settings from the input window."""
    win.config.subject_info(personName=win.user_manager.current_user.name, age = win.user_manager.current_user.age,
                       gender = win.user_manager.current_user.gender )
    
    win.config.display_info(refreshRate=float(win.refreshRateLineEdit.text()), stiLEN=win.keyboard_manager.stim_length, resolution=map(int, win.screenResolutionsLineEdit.text().split('x')), 
                           cubicSize=win.keyboard_manager.current_key_list.cubeSize, imageAddress = 'StimulationSystem'+os.sep+'pics',halfScreen = win.keyboard_manager.halfScreen, halfScreenPos = win.keyboard_manager.halfScreenPos,
                           windowIndex = win.monitorComboBox.currentIndex(), cueTime = win.keyboard_manager.cueTime, maxFrames = win.keyboard_manager.maxFrames)

    win.config.connect_info(COM=win.hardware_manager.COM, streaming_ip=win.hardware_manager.streamingIp, streaming_port=win.hardware_manager.portNumber, 
                           host_ip='127.0.0.1')
 
    #  this must be the last one called!!
    win.config.experiment_info(MODE=win.process_manager.run_mode, targetNUM=len(win.keyboard_manager.current_key_list.keys),
                       blockNum = win.process_manager.num_of_blocks, keyType=win.keyTypeComboBox.currentText(),
                       srate=win.hardware_manager.sampleRate, winLEN=win.process_manager.win_length,
                       paradigm='ssvep', resultPath=win.process_manager.data_saved_path , key_list = win.keyboard_manager.current_key_list, 
                       feature_algo = win.process_manager.feature_extraction, sync_mode = win.process_manager.sync_mode, 
                       p_value = win.process_manager.p_value, chnNUM = win.hardware_manager.chnNUM, chnMontage = win.hardware_manager.chnMontage)
     
    # Save the config object to a file using pickle
    with open("CommonSystem"+os.sep+"config.pkl", "wb") as f:
        pickle.dump(win.config, f, protocol=pickle.HIGHEST_PROTOCOL)
    