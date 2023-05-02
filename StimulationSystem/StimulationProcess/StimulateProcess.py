import time 
from StimulationSystem.StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy import visual, core, event
import datetime
from psychopy.visual.circle import Circle
# import logging

# # configure logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# handler = logging.FileHandler('sti_elapsed_time.log')
# handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(handler)


class StimulateProcess(BasicStimulationProcess):
    def __init__(self) -> None:
        super().__init__()

    def update(self):
        
        self.controller.endBlock = self._checkBlock()
        
        
        self.initFrame.draw()
        if self.MODE !="PREVIEW" and self.MODE != "USE":
            self.controller.dialogue.draw()
            self.controller.feedback.draw()
        self.w.flip()

        # 增加另一个epoch
        self.controller.currentEpochINX += 1
        # 增加另一个epoch
        self.controller.epochThisBlock += 1
        pass

        
    def change(self,result):
        
        self.controller.currentProcess = self.controller.finishProcess
        self.controller.currentResult = result
        # 这里无需改变状态，因为在收到数据之后已经改变过了
        # self.eventController.sendEvent(251)
        self.eventController.clearEvent()



    def run(self):
        
        controller = self.controller
        self.w = controller.w
        
        # stride Text
        if self.strideText != None:
            self.strideText.setText(str(self.controller.key_list.stride))


    
            


        
        
        message = 'STRD'
        
        # print('\nStimulateProcess triggered Operation to identify incoming data, execution time: {}\n'.format(datetime.datetime.now()))
        
        
        
        if self.MODE != 'PREVIEW':
            self.messenger.send_exchange_message(message)
        
        # warm up
        for i in range(10):
            self.w.flip(False)
        
        # do while loop only when self.sync_mode != "Normal", run until self.MODE != 'PREVIEW'
        while self.controller.currentProcess is self and self.controller.end == False:
            
            # core.wait(0.2)
            # frameINX = 0
            startTime = core.getTime()
            # self.trigger_start_time = core.getTime()

                
            # core.wait(0.01)
            frameINX = 0
            if self.sync_mode == "Normal" or  self.MODE == "TRAIN" and self.controller.end == False:

                    
                droppedFrames = self.w.nDroppedFrames
                troubled_frame = []
                self.w.flip(False)
                # Frame dropping check initialization
                self.w.recordFrameIntervals = True
                self.w.flip(False)
                
                while frameINX < len(self.frameSet) :
                    
                    self.frameSet[frameINX].draw()
                    self.w.flip(False)
                    # self.w.flip()
                    
                    if droppedFrames != self.w.nDroppedFrames:
                        troubled_frame.append(frameINX)
                        droppedFrames = self.w.nDroppedFrames
                    
                    if frameINX == 0:
                        if self.MODE != 'PREVIEW':
                            # send trigger
                            self.eventController.sendEvent(self.controller.cueEvent)
                    
                    frameINX += 1
                    
                self.w.recordFrameIntervals = False
                if droppedFrames > 0:
                    subject_name = self.targetPos[self.controller.cueId].personName
                    block = self.controller.currentBlockINX
                    index = self.controller.currentEpochINX
                    cue_id = self.controller.cueId
                    log_frame_drops(subject_name, droppedFrames, troubled_frame, block, index, cue_id)
                print('Overall, %i frames were dropped.' % self.w.nDroppedFrames)
                self.w.nDroppedFrames = 0





            else:
                # able to break from loop once the result is received
                while self.controller.currentProcess is self and self.controller.end == False:
                    frameINX = 0
                    
                    
                    droppedFrames = self.w.nDroppedFrames
                    troubled_frame = []
                    self.w.flip(False)
                    # Frame dropping check initialization
                    self.w.recordFrameIntervals = True
                    self.w.flip(False)

                    while frameINX < len(self.frameSet) :
                        
                        self.frameSet[frameINX].draw()
                        self.w.flip(False)
                        # self.w.flip()
                        
                        if droppedFrames != self.w.nDroppedFrames:
                            troubled_frame.append(frameINX)
                            droppedFrames = self.w.nDroppedFrames
                        
                        if frameINX == 0:
                            if self.MODE != 'PREVIEW':
                                # send trigger
                                self.eventController.sendEvent(self.controller.cueEvent)
                        
                        frameINX += 1
                        
                    self.w.recordFrameIntervals = False
                    if droppedFrames > 0:
                        subject_name = self.targetPos[self.controller.cueId].personName
                        block = self.controller.currentBlockINX
                        index = self.controller.currentEpochINX
                        cue_id = self.controller.cueId
                        log_frame_drops(subject_name, droppedFrames, troubled_frame, block, index, cue_id)
                    print('Overall, %i frames were dropped.' % self.w.nDroppedFrames)
                    self.w.nDroppedFrames = 0

                    
            self.checkEscapeKey()
            
            endTime = core.getTime()
            message = "STI ended in #{:.3f}# seconds".format(endTime - startTime)
            print(message)
            # logger.info(message)
            
            self.w.flip()
            
            if self.controller.key_list.two_phase_on:
                self.twoPhaseBox.draw()
            self.initFrame.draw()
            
            if self.strideText != None:
                self.strideText.draw()
            
            if self.MODE != "PREVIEW" and self.MODE != "USE":
                self.controller.dialogue.draw()
                self.controller.feedback.draw()
            self.w.flip(False)
            
            self.eventController.clearEvent()
            
            if self.sync_mode == "Normal" or self.MODE == "TRAIN":
                break # only run maximum one time
        
        # while end
        
        if self.MODE != 'PREVIEW':
            while self.controller.currentProcess is self:
                # 如果刺激结束了，还没有收到结果，就先进入等待
                core.wait(0.01)
        else:
            self.change(None)
            
        self.update()
        
        
    def _checkBlock(self):

        if self.controller.blockCueINX == []:
            self.controller.currentBlockINX += 1
            return True
        else:
            return False
        
def log_frame_drops(subject_name, no_of_frames, dropped_frames, block, index, cue_id):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = {
        "subject_name": subject_name,
        "timestamp": current_time,
        "number_of_frames": no_of_frames,
        "dropped_frames": dropped_frames,
        "block": block,
        "index": index,
        "cue_id": cue_id,
    }
    log_message = "Subject: {subject_name}, Timestamp: {timestamp}, No of Frames: {number_of_frames},Dropped Frames: {dropped_frames}, Block: {block}, Index: {index}, Cue ID: {cue_id}".format(**log_data)
    print(log_message)
    with open("frame_drops.log", "a") as log_file:
        log_file.write(log_message + "\n")
