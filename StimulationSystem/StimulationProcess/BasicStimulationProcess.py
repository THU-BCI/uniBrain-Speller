from abc import abstractmethod
from psychopy import visual
from psychopy.hardware import keyboard
from StimulationSystem.EventController import EventController

class BasicStimulationProcess:
    """
    BasicStimulationProcess is an abstract base class that defines the structure for the different 
    stimulation processes: Idle, Prepare, Stimulate, and Finish.
    """
    def __init__(self):
        self.twoPhaseBox = None

    @abstractmethod
    def initial(self, controller, viewContainer, messenger):
        """
        Initialize the process with the given controller, viewContainer, and messenger.
        This method is expected to be overridden by child classes.
        """
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
        self.trigger_start_time = None
        self.twoPhaseBox = viewContainer.twoPhaseBox
        self.strideText = viewContainer.strideText
        self.kb = keyboard.Keyboard()

    @abstractmethod
    def update(self):
        """
        Abstract method to update the state of the process.
        This method is expected to be overridden by child classes.
        """
        pass

    @abstractmethod
    def change(self):
        """
        Abstract method to change the state of the process.
        This method is expected to be overridden by child classes.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Abstract method to run the main logic of the process.
        This method is expected to be overridden by child classes.
        """
        pass

    def drawDialogue(self, text, color, fillColor):
        """
        Create and return a TextBox2 object with the specified text, color, and fillColor.
        """
        dialogue = visual.TextBox2(
            self.w, text=text, font='Meslo LG M DZ', units='pix',
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
            autoLog=True,
        )

        return dialogue

    def checkEscapeKey(self):
        """
        Check if the escape key is pressed. If pressed, set the controller's end attribute to True.
        """
        keys = self.kb.getKeys(['escape'])
        if 'escape' in keys:
            print("Escape key pressed. Exiting...")
            self.controller.end = True
