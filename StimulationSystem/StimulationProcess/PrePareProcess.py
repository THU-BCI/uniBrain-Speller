from StimulationSystem.StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy.visual.rect import Rect
from psychopy.visual.circle import Circle
from psychopy import core

class PrepareProcess(BasicStimulationProcess):
    """
    The PrepareProcess class is responsible mainly for showing the cue and preparing the next flickering stimuli to the participant.
    It inherits from the BasicStimulationProcess abstract base class.
    
    Attributes:
        Inherits attributes from the BasicStimulationProcess class.
        
    Methods:
        __init__(): Initializes the PrepareProcess instance.
        change(): Changes the state of the process to the stimulate process.
        run(): Main logic of the prepare process.
        _showCue(id): Draws the initial texture and shows the result.
    """
    def __init__(self) -> None:
        super().__init__()

    def change(self):
        """Change the state from prepare to stimulate."""
        self.controller.currentProcess = self.controller.stimulateProcess

    def run(self):
        """Run the prepare process."""

        # Pop a cue
        if self.MODE == "USE":
            self.controller.cueId = -1
            self.controller.cueEvent = 99
        else:
            self.controller.cueId = self.controller.blockCueINX.pop(0)
            self.controller.cueEvent = self.controller.blockCueEvent.pop(0)

        self.controller.w = self._showCue(self.controller.cueId)
        self.checkEscapeKey()
        self.change()

    def _showCue(self, id):
        """
        Draw initial texture and show result.

        :param id: The cue id.
        :return: The window object.
        """

        if self.strideText is not None:
            self.strideText.setText(str(self.controller.key_list.stride))

        if self.MODE != "USE":
            pos = self.targetPos[id].position

            # Dot
            circle = Circle(win=self.w, pos=[pos[0], pos[1] - self.cubicSize / 2 - 20], radius=5, fillColor='red',
                            units='pix')

            # Red circumferential rectangle
            rect = Rect(win=self.w, pos=pos, width=self.cubicSize,
                        height=self.cubicSize, units='pix', fillColor='red')

        if self.MODE == "PREVIEW":
            if self.twoPhaseBox is not None:
                self.twoPhaseBox.draw()

            self.initFrame.draw()
            rect.draw()

            if self.strideText is not None:
                self.strideText.draw()

            self.w.flip()
            core.wait(self.cueTime / 2)

            if self.twoPhaseBox is not None:
                self.twoPhaseBox.draw()

            self.initFrame.draw()
            circle.draw()

            if self.strideText is not None:
                self.strideText.draw()

            self.w.flip(False)
            core.wait(self.cueTime / 2)

        elif self.MODE == "USE":
            if self.controller.key_list.two_phase_on:
                self.twoPhaseBox.draw()
            self.initFrame.draw()

            if self.strideText is not None:
                self.strideText.draw()

            self.w.flip(False)

        else:
            self.initFrame.draw()
            self.controller.dialogue.draw()
            self.controller.feedback.draw()
            rect.draw()

            if self.strideText is not None:
                self.strideText.draw()

            self.w.flip()
            core.wait(self.cueTime / 2)

            self.initFrame.draw()
            self.controller.dialogue.draw()
            self.controller.feedback.draw()
            circle.draw()

            if self.strideText is not None:
                self.strideText.draw()

            self.w.flip(False)
            core.wait(self.cueTime / 2)

        return self.w
