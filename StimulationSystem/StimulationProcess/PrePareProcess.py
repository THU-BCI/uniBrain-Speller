import time
import os
# get current directory
current_path  = os.getcwd()
# print(current_path)
# relative path to add
relative_path = "StimulationSystem"

# join paths to get full path
full_path = os.path.join(current_path, relative_path)

# add the path to the system paths
import sys
sys.path.append(full_path)

from StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy.visual.rect import Rect
from psychopy.visual.circle import Circle
from psychopy.visual import TextBox2
from psychopy import visual,core
import matplotlib.pyplot as plt

class PrepareProcess(BasicStimulationProcess):
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
