from numpy import place
from StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy.visual.rect import Rect
from psychopy.visual.circle import Circle
from psychopy import core

    def change(self):

        if self.controller.endBlock:
            self.controller.currentProcess = self.controller.idleProcess
            self.controller.historyString = []
        else:
            self.controller.currentProcess = self.controller.prepareProcess

    def run(self):
        
        
        # showFeedback 负责把判决结果显示在对话框
        if self.MODE == "PREVIEW":
            self.controller.endBlock = True
            self.controller.end = True
        elif self.MODE == "TRAIN" or self.MODE == "TEST":
            if self.controller.currentResult == 0: # means a training process
                id = self.events.index(self.controller.cueEvent)
            else:
                id = self.events.index(self.controller.currentResult)
                
            self._showFeedback(id)

            # Calculate elapsed time
            # elapsed_time =  "{:.3f}".format(time.time() - self.controller.stimulateProcess.trigger_start_time)

            # Print elapsed time
            # print()
            # print(f"Elapsed time between triggering and getting the result: #{elapsed_time}# seconds")
            # Log elapsed time
            #self.log.info(f"Elapsed time between triggering and getting the result: #{elapsed_time}# seconds")
            
        elif self.MODE == "USE":
            
            id = self.events.index(self.controller.currentResult)
            # Calculate elapsed time
            # elapsed_time =  "{:.3f}".format(time.time() - self.controller.stimulateProcess.trigger_start_time)

            # Print elapsed time
            # print()
            # print(f"Elapsed time between triggering and getting the result: #{elapsed_time}# seconds")
            # Log elapsed time
            #self.log.info(f"Elapsed time between triggering and getting the result: #{elapsed_time}# seconds")
            
            # initiate work            
            # self.controller.key_list.keys[id].run_key_function(self.controller.key_list)
            # initiate work            
            self.controller.key_list.keys[id].run_key_function(self.controller.key_list, wait = True)
            
            
            # initialization
            pos = self.targetPos[id].position
        
            # dot
            circle = Circle(win=self.w, pos=[pos[0], pos[1] - self.cubicSize/2-20], radius=5, fillColor='red', units='pix')
            
            # red circumcing rectangle
            rect = Rect(win=self.w, pos=pos, width=self.cubicSize,
                        height=self.cubicSize, units='pix', fillColor='red')
            
            if self.strideText != None:
                self.strideText.setText(str(self.controller.key_list.stride))
            
            # show result
            if self.controller.key_list.two_phase_on:
                self.twoPhaseBox.draw()
            self.initFrame.draw()
            rect.draw()
            if self.strideText != None:
                self.strideText.draw()
            self.w.flip()
            core.wait(self.cueTime/2)
            
            self.initFrame.draw()
            circle.draw()
            if self.strideText != None:
                self.strideText.draw()
            self.w.flip()
            
            core.wait(self.cueTime/2)
            # Forever run!
            self.controller.currentBlockINX = 0 
            
        elif self.MODE =="DEBUG":
            
            id = self.events.index(self.controller.currentResult)
            
            # initiate work            
            # self.controller.key_list.keys[id].run_key_function(self.controller.key_list, wait = True)
            self.controller.key_list.keys[id].run_key_function(self.controller.key_list)
        
            self._showFeedback(id)
            

            # Calculate elapsed time
            # elapsed_time =  "{:.3f}".format(time.time() - self.controller.stimulateProcess.trigger_start_time)

            # Print elapsed time
            # print()
            # print(f"Elapsed time between triggering and getting the result: #{elapsed_time}# seconds")
            
        # these two modes won't contribute towards the output count
        if self.MODE != "PREVIEW" and self.MODE != "TRAIN":
            count = self.controller.progress_manager["output_count"]
            count[id] += 1
            # print(self.controller.progress_manager["output_count"])
            self.controller.progress_manager["output_count"]  = count
            # print(self.controller.progress_manager["output_count"])
        
        
        self.checkEscapeKey()
        self.change()

        pass

    def _showFeedback(self,currentResult):
        
        
        # stride Text
            
        if self.strideText != None:
            self.strideText.setText(str(self.controller.key_list.stride))

        
        epochINX = self.controller.epochThisBlock    

        # result in this epoch 再画当前试次的结果
        resultChar = self.char[currentResult]
        resultChar = '%s'%(resultChar)
        # placeholder代表给之前的试次留空位
        placeholder = ''
        for _ in range(epochINX-1):
            placeholder = placeholder + ' '
        resultText = placeholder+resultChar
        
        charColor = 'white'
        result = self.drawDialogue(resultText, color=charColor,fillColor=None)
        
        # print(str(self.testValue))
        
        self.initFrame.draw()
        if self.strideText != None:
            self.strideText.draw()
        self.controller.dialogue.draw()
        self.controller.feedback.draw()
        result.draw()
        self.w.flip()
        core.wait(0.3)
        
        
        # 更新一下feedback，当前的feedback已经包含当前试次了，等待下一个试次再画上
        histroString = self.controller.historyString  
        feedbackText = ''.join(histroString)
        feedback = self.drawDialogue(feedbackText+resultChar,color='white',fillColor=None)
        self.controller.historyString.append(resultChar)
        self.controller.feedback = feedback
        

        return
