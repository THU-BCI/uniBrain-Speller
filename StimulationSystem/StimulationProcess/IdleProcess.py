import time
from typing import Text
import numpy as np
from StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy import event, visual, core


class IdleProcess(BasicStimulationProcess):
    def __init__(self) -> None:
        super().__init__()

    def change(self):

        self.controller.currentProcess = self.controller.prepareProcess

    def run(self):
        
        # 本节实验结束界面
        self._idleInterface()
        
        if self.controller.end == False:
        # 等待键盘输入继续
            if self.MODE != "PREVIEW": # skip the idle interface in preview mode
                event.waitKeys(keyList=['space'])
                # A=1

        # 更新当前block的信息
            self.update()
            self.eventController.clearEvent()

        core.wait(1)
        
        self.change()

    def _idleInterface(self):

        self.w.flip()
        if self.controller.currentBlockINX == 0:
            if self.MODE =="TRAIN":
                text = 'Train mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE =="TEST":
                text = 'Test mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE =="USE":
                text = 'Usage mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE =="DEBUG":
                text = 'Debug mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            else: # PREVIEW  
                text = ""
        elif self.controller.currentBlockINX == len(self.cueIndices):
            text = 'The process is done!\n\nThank you.'
            self.controller.end = True
        else:
            text = 'Section %s of the process has ended.\n\n\nPlease press the spacebar to continue the experiment after the break.' % self.controller.currentBlockINX
        text = visual.TextStim(self.w, pos=[0, 0], text=text, color=(255, 255, 255),
                               colorSpace='rgb255')
        text.draw()

        self.w.flip()

        self.controller.endBlock = False
        self.checkEscapeKey()

        pass

    def update(self):
        
        self.w.flip()
        
        self.controller.epochThisBlock = 0

        currentBlockINX = self.controller.currentBlockINX
        self.controller.blockCueINX = self.cueIndices[currentBlockINX]
        self.controller.blockCueEvent = self.cueEvents[currentBlockINX]
        self.controller.blockCueText = self.cueText[currentBlockINX]
        text = ''.join(self.cueText[currentBlockINX])

        self.controller.feedback = None

        self.initFrame.draw()
        
        if self.MODE != "PREVIEW" and self.MODE != "USE":
            self.controller.dialogue = self.drawDialogue(
                text, color='gray', fillColor=None)
            self.controller.dialogue.draw()

        self.w.flip()
        
        self.controller.w = self.w
        self.controller.endBlock = False
        
        if self.MODE != "PREVIEW" and self.MODE != "USE":
            self.controller.feedback = self.drawDialogue(
                "", color='White', fillColor=None)
        return

    def _openEyes(self):
        self.w.flip()

        text = visual.TextStim(
            self.w, pos=[0, 0], text='请注释屏幕中央的标记，保持视线稳定',
            color=(255, 255, 255), colorSpace='rgb255'
        )
        text.draw()
        self.w.flip()

        core.wait(1)

        cross = visual.ShapeStim(
            win=self.w, name='polygon', vertices='cross',
            size=(50, 50),
            ori=0.0, pos=(0, 0),
            lineWidth=1.0,     colorSpace='rgb',  lineColor='white', fillColor='white',
            opacity=None, depth=0.0, interpolate=True)

        cross.draw()
        self.w.flip()
        core.wait(1)

        pass

    def _closeEyes(self):

        text = visual.TextStim(
            self.w, pos=[0, 0], text='请闭眼',
            color=(255, 255, 255), colorSpace='rgb255'
        )
        text.draw()

        self.w.flip()

        core.wait(1)

        pass
