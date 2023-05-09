from StimulationSystem.StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy.visual.rect import Rect
from psychopy.visual.circle import Circle
from psychopy import core


class FinishProcess(BasicStimulationProcess):
    """
    The FinishProcess class manages the end of the stimulation process in different modes (PREVIEW, TRAIN, TEST, USE, DEBUG).
    It displays results and performs outputs based on the evaluation of the process. It inherits from the BasicStimulationProcess
    abstract base class.

    Attributes:
        Inherits attributes from the BasicStimulationProcess class.
        
    Methods:
        __init__(): Initializes the FinishProcess instance.
        change(): Changes the state of the process based on the endBlock status.
        run(): Runs the finish process based on the current mode and handles the results accordingly.
        handle_train_test_mode(): Handles the logic for the TRAIN and TEST modes.
        handle_use_mode(): Handles the logic for the USE mode.
        handle_debug_mode(): Handles the logic for the DEBUG mode.
        _showFeedback(currentResult): Shows feedback for the current result.
    """
    def __init__(self) -> None:
        super().__init__()

    def change(self):
        """
        Change the current process based on the endBlock status.
        """
        if self.controller.endBlock:
            self.controller.currentProcess = self.controller.idleProcess
            self.controller.historyString = []
        else:
            self.controller.currentProcess = self.controller.prepareProcess
            
    def run(self):
        """
        Run the finish process based on the current mode and handle the results accordingly.
        """
        if self.MODE == "PREVIEW":
            self.controller.endBlock = True
            self.controller.end = True
        elif self.MODE == "TRAIN" or self.MODE == "TEST":
            id = self.handle_train_test_mode()
        elif self.MODE == "USE":
            id = self.handle_use_mode()
        elif self.MODE =="DEBUG":
            id = self.handle_debug_mode()

        # Update output count if not in PREVIEW or TRAIN mode
        if self.MODE != "PREVIEW" and self.MODE != "TRAIN":
            count = self.controller.progress_manager["output_count"]
            count[id] += 1
            self.controller.progress_manager["output_count"]  = count

        self.checkEscapeKey()
        self.change()
        
    def handle_train_test_mode(self):
        """
        Handle the logic for the TRAIN and TEST modes.
        """
        if self.controller.currentResult == 0: # means a training process
            id = self.events.index(self.controller.cueEvent)
        else:
            id = self.events.index(self.controller.currentResult)

        self._showFeedback(id)
        
        return id
        
    def handle_use_mode(self):
        """
        Handle the logic for the USE mode.
        """
        id = self.events.index(self.controller.currentResult)

        self.controller.key_list.keys[id].run_key_function(self.controller.key_list, wait = True)

        pos = self.targetPos[id].position
        circle = Circle(win=self.w, pos=[pos[0], pos[1] - self.cubicSize/2-20], radius=5, fillColor='red', units='pix')
        rect = Rect(win=self.w, pos=pos, width=self.cubicSize, height=self.cubicSize, units='pix', fillColor='red')

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
        
        return id

    def handle_debug_mode(self):
        """
        Handle the logic for the DEBUG mode.
        """
        id = self.events.index(self.controller.currentResult)

        self.controller.key_list.keys[id].run_key_function(self.controller.key_list)

        self._showFeedback(id)
        
        return id

    def _showFeedback(self, currentResult):
        """
        Show feedback for the current result.

        :param currentResult: Index of the current result to display
        """
        # Update stride text if not None
        if self.strideText != None:
            self.strideText.setText(str(self.controller.key_list.stride))

        epochINX = self.controller.epochThisBlock

        # Result character for the current epoch
        resultChar = self.char[currentResult]
        resultChar = '%s' % (resultChar)
        # Placeholder for previous epochs
        placeholder = ''
        for _ in range(epochINX-1):
            placeholder = placeholder + ' '
        resultText = placeholder + resultChar

        charColor = 'white'
        result = self.drawDialogue(resultText, color=charColor, fillColor=None)

        self.initFrame.draw()
        if self.strideText != None:
            self.strideText.draw()
        self.controller.dialogue.draw()
        self.controller.feedback.draw()
        result.draw()
        self.w.flip()
        core.wait(0.3)

        # Update feedback for the next epoch
        histroString = self.controller.historyString
        feedbackText = ''.join(histroString)
        feedback = self.drawDialogue(feedbackText + resultChar, color='white', fillColor=None)
        self.controller.historyString.append(resultChar)
        self.controller.feedback = feedback

        return