from StimulationSystem.StimulationProcess.viewContainer import viewContainer
from StimulationSystem.StimulationProcess.PrePareProcess import PrepareProcess
from StimulationSystem.StimulationProcess.StimulateProcess import StimulateProcess
from StimulationSystem.StimulationProcess.FinishProcess import FinishProcess
from StimulationSystem.StimulationProcess.IdleProcess import IdleProcess
from psychopy import visual
from psychopy.visual.rect import Rect
import os
import pickle
import numpy as np
import math

class StimulationController:
    def __init__(self):
        # 各个状态
        self.initialProcess = None
        self.prepareProcess = None
        self.stimulateProcess = None
        self.idleProcess = None
        self.finishProcess = None
        self.currentProcess = None
        
        # 显示界面
        self.w = None
        
        self.endBlock = False
        self.endSession = None

        # 当前epoch的cue
        self.cueId = None   
        # 当前block的提示编号
        self.blockCues = None
        # 当前block提示字符
        self.blockCueText = None
        # 当前epoch的编号
        self.currentEpochINX = 0
        # 当前block内epoch的编号
        self.epochThisBlock = 0
        # 当前block的编号
        self.currentBlockINX = 0
        # 当前epoch的结果（由operation返回）
        self.currentResult = None
        # 用户打字的字符框反馈
        self.feedback = None
        # 字符映射
        self.end = False
        
        self.timeStamp = None
        
        self.twoPhaseBox = None
        
        self.key_list = None
        
        self.progress_manager = None
        
        


    def initial(self, config, messenger, progress_manager = None, loadPicsBool = True):
        
        self.messager = messenger
        
        if loadPicsBool == True:
        
            viewcontainer = viewContainer(config)
            
            self.viewContainer = viewcontainer
            
            self.loadPics(config, progress_manager)
            
        self.key_list = viewcontainer.key_list
        
        self.resetProcess(config,messenger)
        
        self.progress_manager = progress_manager 
        
        return self
    
    def resetProcess(self,config,messenger):
        
        
        # 准备阶段：展示cue，展示上次结果
        self.prepareProcess = PrepareProcess()
        self.prepareProcess.initial(self, self.viewContainer, messenger)

        # 开始刺激：刺激时展示cue
        self.stimulateProcess = StimulateProcess()
        self.stimulateProcess.initial(self, self.viewContainer, messenger)

        # 结束刺激：展示结果？
        self.finishProcess = FinishProcess()
        self.finishProcess.initial(self, self.viewContainer, messenger)

        # Block间的空闲状态
        self.idleProcess = IdleProcess()
        self.idleProcess.initial(self, self.viewContainer, messenger)
        
        self.currentProcess = self.idleProcess
        return self
        

    def loadPics(self,config,progress_manager = None):
    
        addSTI = config.addSTI
        
        x_resolution, y_resolution = config.resolution
        
        if config.halfScreen == False:

            window = visual.Window((x_resolution, y_resolution), monitor="testMonitor", units="pix", fullscr=True,
                                waitBlanking=True, color=(0, 0, 0), colorSpace='rgb255', screen=config.windowIndex,
                                allowGUI=False, useFBO=True)
        else:
            half_width = x_resolution // 2
            half_height = y_resolution // 2
            

            if config.halfScreenPos == 0:
                if config.key_list.MouseOrKeyboard == "Mouse":
                    # left half
                    x_resolution = half_width
                    window = visual.Window((x_resolution, y_resolution), fullscr=False, monitor="testMonitor", units="pix",
                                        pos=(0, 0), color=(0, 0, 0), colorSpace='rgb255', waitBlanking=True,
                                        screen=config.windowIndex, allowGUI=False, useFBO=True)
                else:
                    # bottom half
                    y_resolution = half_height
                    window = visual.Window((x_resolution, y_resolution), fullscr=False, monitor="testMonitor", units="pix",
                                        pos=(0, half_height), color=(0, 0, 0), colorSpace='rgb255', waitBlanking=True,
                                        screen=config.windowIndex, allowGUI=False, useFBO=True)
                    
            else:
                if config.key_list.MouseOrKeyboard == "Mouse":
                    # right half
                    x_resolution = half_width
                    window = visual.Window((x_resolution, y_resolution), fullscr=False, monitor="testMonitor", units="pix",
                                        pos=(half_width, 0), color=(0, 0, 0), colorSpace='rgb255', waitBlanking=True,
                                        screen=config.windowIndex, allowGUI=False, useFBO=True)
                else:
                    # top half
                    y_resolution = half_height
                    window = visual.Window((x_resolution, y_resolution), fullscr=False, monitor="testMonitor", units="pix",
                                        pos=(0, 0), color=(0, 0, 0), colorSpace='rgb255', waitBlanking=True,
                                        screen=config.windowIndex, allowGUI=False, useFBO=True)

        if config.halfScreen == False:
            # Measure the actual refresh rate (returns value in Hz)
            actual_frame_rate = window.getActualFrameRate()

            print("Actual refresh rate: {:.2f} Hz".format(actual_frame_rate))

            # allow a 4 ms tolerance; any refresh that takes longer than the specified 
            # period will be considered a "dropped" frame and increase the count of 
            # win.nDroppedFrames.
            window.refreshThreshold = 1 / actual_frame_rate + 0.004  
        else:
            window.refreshThreshold = 1 / config.refreshRate + 0.004  
        
        
        maxFrames = int(config.stiLEN * config.refreshRate)
        
        
        
        frameSet = []
        
        # initial frame
        add = config.addSTI + os.sep + 'initial_frame.png'
        initFrame = visual.ImageStim(window, image=add, pos=[0, 0], size=[
                                    x_resolution, y_resolution], units='pix', flipVert=False)

        # stimulation frames
        
        if progress_manager != None:
            progress_manager["text"] = "Psychopy loading pictures... please wait..."
        
        
        
        rectSet_data = config.addSTI + os.sep + 'STI.pkl'
        
        # Load rectSet saved in pickle        
        with open(rectSet_data, "rb") as fp:
            rectSet = pickle.load(fp)
        
            
        n_elements = len(rectSet)

        
        
        stim_colors = np.zeros((maxFrames+1, n_elements, 3))
        stim_pos = np.zeros((n_elements, 2))
        
        total_iterations = len(rectSet) * (maxFrames + 1)
        current_iteration = 0

        for i, rect in enumerate(rectSet):
            
            position = rect.covert2psycho(x_res = x_resolution, y_res = y_resolution)
            stim_pos[i,:] = np.array(position)
            rect.position = position

            for N in range(maxFrames+1):
                # 每一帧的每一个目标
                if N == 0:
                    brightness = 1
                else:
                    brightness = 0.5 + 0.5 * math.sin( 2 * math.pi * rect.frequency /config.refreshRate * (N-1) + rect.start_phase )
                
                stim_colors[N, i, :] = [brightness, brightness, brightness]

                
                current_iteration += 1
                progress_manager["value"] = (current_iteration / total_iterations) * 100

        

        stim_sizes = np.ones((n_elements,)) * config.cubicSize
        
        for frame in range(maxFrames+1):
            color = stim_colors[frame, ...]
            stim = visual.ElementArrayStim(
                win=window,
                units='pix',
                nElements=n_elements,
                sizes=stim_sizes,
                xys=stim_pos,
                colors=color,
                colorSpace='rgb',
                elementTex=np.ones((64, 64)),
                elementMask=None,
                texRes=256
            ) 
            if frame != 0:
                frameSet.append(stim)
        # frameSet.pop[0]
            
            
        # confirm the stride text position
        if config.key_list.MouseOrKeyboard == "Mouse":
            plus_key = None
            minus_key = None
            
            # Find the keys with names "+" and "-"
            for key in config.key_list.keys:
                if key.key_name == "+":
                    plus_key = key
                elif key.key_name == "-":
                    minus_key = key
            
            # Calculate the middle of location_x and location_y values
            if plus_key and minus_key:
                middle_location_x = (plus_key.location_x + minus_key.location_x) / 2
                middle_location_y = (plus_key.location_y + minus_key.location_y) / 2
                config.strideTextPos = covert2psycho(config.cubicSize,middle_location_x, middle_location_y,x_res = x_resolution, y_res = y_resolution)
            else:
                config.strideTextPos = None
        else: 
            config.strideTextPos = None
        
        # confirm the two phase rectangle position        
        if config.key_list.MouseOrKeyboard == "Mouse":
            dragKey = None
            
            # Find the keys with names "+" and "-"
            for key in config.key_list.keys:
                if key.key_name == "Drag":
                    dragKey = key
            # Calculate the middle of location_x and location_y values
            if dragKey:
                config.twoPhaseRectPos = covert2psycho(config.cubicSize,dragKey.location_x, dragKey.location_y,x_res = x_resolution, y_res = y_resolution)
            else:
                config.twoPhaseRectPos = None
        else: 
            shiftKey = None
            # Find the keys with names "+" and "-"
            for key in config.key_list.keys:
                if key.key_name == "⇧":
                    shiftKey = key
            # Calculate the middle of location_x and location_y values
            if shiftKey:
                config.twoPhaseRectPos = covert2psycho(config.cubicSize,shiftKey.location_x, shiftKey.location_y,x_res = x_resolution, y_res = y_resolution)
                
            else:
                self.twoPhaseRectPos = None
            
        if config.strideTextPos != None:
            strideText = visual.TextStim(window, pos=config.strideTextPos, text=str(config.key_list.stride), color=(255, 255, 255),
                                            colorSpace='rgb255', height=int(config.cubicSize*2/3), units='pix')
        else:
            strideText = None
            
            
        if config.twoPhaseRectPos != None:
            twoPhaseBox = Rect(win=window, pos=config.twoPhaseRectPos, width=config.cubicSize*1.2,
                        height=config.cubicSize*1.2, units='pix', fillColor='blue')
        else:
            twoPhaseBox = None
            

        self.viewContainer.strideText = strideText
        self.viewContainer.twoPhaseBox = twoPhaseBox
        self.viewContainer.w = window
        self.viewContainer.frameSet = frameSet
        self.viewContainer.initFrame = initFrame        
        self.viewContainer.targetPos = rectSet
        self.viewContainer.x_res = x_resolution
        self.viewContainer.y_res = y_resolution
        
        return self
        
    def run(self):
        if self.end == False:
            self.currentProcess.run()
        else:
            self.w.close()
            


def covert2psycho(rect_size,x,y,x_res = 1920,y_res = 1080):
    width = rect_size/2
    
    out_x = x-x_res/2 + width
    out_y = y-y_res/2 + width

    return [out_x,out_y]