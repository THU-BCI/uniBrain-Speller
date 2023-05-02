from abc import ABCMeta, abstractmethod
# from psychopy.visual.circle import Circle
from psychopy import visual
from psychopy.hardware import keyboard
# from psychopy import core, event
from EventController import EventController

import time


class BasicStimulationProcess:

    def __init__(self) -> None:
        self.twoPhaseBox = None
        pass

    @abstractmethod
    def initial(self, controller, viewContainer, messenger):

        self.controller = controller
        
        self.MODE = viewContainer.MODE
        self.sync_mode = viewContainer.sync_mode
        self.messenger = messenger
        if self.MODE != 'PREVIEW':
            self.messenger.exchange_message_operator.controller = self.controller

        self.w = viewContainer.w

        self.initFrame = viewContainer.initFrame
        self.frameSet = viewContainer.frameSet

        self.controller.historyString = []
        self.char = viewContainer.char
        self.events = viewContainer.events
        self.targetPos = viewContainer.targetPos
        self.stringPos = viewContainer.stringPos
        self.paradigm = viewContainer.paradigm

        self.cueIndices = viewContainer.cueIndices
        self.cueEvents = viewContainer.cueEvents
        self.cubicSize = viewContainer.cubicSize
        self.cueTime = viewContainer.cueTime
        self.targetNUM = viewContainer.targetNUM
        self.cueText = viewContainer.displayChar
        self.COM = viewContainer.COM
        self.x_res = viewContainer.x_res
        self.y_res = viewContainer.y_res
        
        self.eventController = EventController(COM=self.COM)
        
        # self.twoPhaseRectPos =  viewContainer.twoPhaseRectPos
        # self.strideTextPos = viewContainer.strideTextPos
        
        self.trigger_start_time = None
        self.twoPhaseBox = viewContainer.twoPhaseBox
        self.strideText = viewContainer.strideText
        # self.drawTwoPhasePrepare()
        
        # 创建键盘对象
        self.kb = keyboard.Keyboard()
        pass

    @abstractmethod
    def update(self):

        pass

    @abstractmethod
    def change(self):

        pass

    @abstractmethod
    def run(self):

        pass

    def drawDialogue(self, text, color, fillColor):
        
        # self.x_res
        # self.y_res
        dialogue = visual.TextBox2(
            self.w, text=text, font='Meslo LG M DZ', units='pix',
            # pos=(-735, 525), letterHeight=50.0,
            # size=(1470, 50), borderWidth=2.0,
            pos=(-self.x_res/3, self.y_res/2), letterHeight=50.0,
            size=(self.x_res, 50), borderWidth=2.0,
            color=color, colorSpace='rgb',
            opacity=None,
            bold=False, italic=False,
            lineSpacing=1.0,
            padding=0.0, alignment='top-left',
            anchor='top-left',
            fillColor=fillColor, borderColor=None,
            editable=False,
            autoLog=True,)

        return dialogue
    
    # def drawTwoPhasePrepare(self):
        
    #     # circumcing rectangle
    #     if self.twoPhaseRectPos != None:
    #         self.twoPhaseBox = visual.Rect(win=self.w, pos=self.twoPhaseRectPos, width=self.cubicSize*1.2,
    #                     height=self.cubicSize*1.2, units='pix', fillColor='blue')
    #     else:
    #         self.twoPhaseBox = None
        
    #     pass
    
    def checkEscapeKey(self):
        keys = self.kb.getKeys(['escape'])
        if 'escape' in keys:
            print("Escape key pressed. Exiting...")
            self.controller.end = True
            
        