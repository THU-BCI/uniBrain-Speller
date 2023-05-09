from typing import Text
from StimulationSystem.StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy import event, visual, core


class IdleProcess(BasicStimulationProcess):
    """
    The IdleProcess class represents a resting state between loops of the stimulation process. 
    It serves as a "crossroads" for determining the next steps in the process. It inherits from the 
    BasicStimulationProcess abstract base class.
    
    Attributes:
        Inherits attributes from the BasicStimulationProcess class.
        
    Methods:
        __init__(): Initializes the IdleProcess instance.
        change(): Changes the state of the process to the prepare process.
        run(): Main logic of the idle process.
        _idleInterface(): Displays the idle interface.
        update(): Updates the current block information.
        _openEyes(): Displays the 'please focus on the center of the screen' message.
        _closeEyes(): Displays the 'please close your eyes' message.
    """
    def __init__(self) -> None:
        super().__init__()


    def change(self):
        """Switches to the prepare process."""
        self.controller.currentProcess = self.controller.prepareProcess


    def run(self):
        """Runs the idle process."""
        # Display end-of-section interface
        self._idleInterface()

        if not self.controller.end:
            # Wait for keyboard input to continue
            if self.MODE != "PREVIEW":  # skip the idle interface in preview mode
                # event.waitKeys(keyList=['space'])
                passWait = True

            # Update current block information
            self.update()
            self.eventController.clearEvent()

        core.wait(1)

        self.change()


    def _idleInterface(self):
        """Displays the idle interface."""
        self.w.flip()
        if self.controller.currentBlockINX == 0:
            if self.MODE == "TRAIN":
                text = 'Train mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE == "TEST":
                text = 'Test mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE == "USE":
                text = 'Usage mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            elif self.MODE == "DEBUG":
                text = 'Debug mode is about to begin, please remain calm.\n\nPress the spacebar to continue.'
            else:  # PREVIEW
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


    def update(self):
        """Updates the current block information."""
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
        """Displays the 'please focus on the center of the screen' message."""
        self.w.flip()

        text = visual.TextStim(
            self.w, pos=[0, 0], text='Please focus on the center of the screen and maintain a steady gaze',
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


    def _closeEyes(self):
        """Displays the 'please close your eyes' message."""
        text = visual.TextStim(
            self.w, pos=[0, 0], text='Please close your eyes',
            color=(255, 255, 255), colorSpace='rgb255'
        )
        text.draw()

        self.w.flip()

        core.wait(1)
