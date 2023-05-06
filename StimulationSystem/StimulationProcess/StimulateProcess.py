import time
from StimulationSystem.StimulationProcess.BasicStimulationProcess import BasicStimulationProcess
from psychopy import core
import datetime


class StimulateProcess(BasicStimulationProcess):
    """
    The StimulateProcess class is responsible for presenting the flickering stimuli to the participant.
    It inherits from the BasicStimulationProcess abstract base class.
    
    Attributes:
        Inherits attributes from the BasicStimulationProcess class.
        
    Methods:
        __init__(): Initializes the StimulateProcess instance.
        update(): Updates the state of the stimulation process.
        change(result): Changes the state of the process to the finish process and clears events.
        run(): Main logic of the stimulation process.
        _checkBlock(): Checks whether the current block of cues is finished.
    """
    def __init__(self) -> None:
        super().__init__()

    def update(self):
        # Check if the current block of stimuli has ended and update the endBlock attribute of the controller
        self.controller.endBlock = self._checkBlock()

        # Draw the initial frame and display dialogue and feedback
        self.initFrame.draw()
        if self.MODE != "PREVIEW" and self.MODE != "USE":
            self.controller.dialogue.draw()
            self.controller.feedback.draw()
        self.w.flip()

        # Increment the current epoch index and the number of epochs in the current block
        self.controller.currentEpochINX += 1
        self.controller.epochThisBlock += 1

    def change(self, result):
        # Change the current process to the finish process and store the result
        self.controller.currentProcess = self.controller.finishProcess
        self.controller.currentResult = result
        self.eventController.clearEvent()


    def run(self):
        # Main method to run the stimulation process
        controller = self.controller
        self.w = controller.w

        if self.strideText is not None:
            self.strideText.setText(str(self.controller.key_list.stride))

        message = 'STRD'

        if self.MODE != 'PREVIEW':
            self.messenger.send_exchange_message(message)

        for i in range(10):
            self.w.flip(False)

        while self.controller.currentProcess is self and self.controller.end == False:

            startTime = core.getTime()
            frameINX = 0

            if self.sync_mode == "Normal" or self.MODE == "TRAIN" and self.controller.end == False:

                droppedFrames = self.w.nDroppedFrames
                troubled_frame = []
                self.w.flip(False)
                self.w.recordFrameIntervals = True
                self.w.flip(False)

                while frameINX < len(self.frameSet):

                    self.frameSet[frameINX].draw()
                    self.w.flip(False)

                    if droppedFrames != self.w.nDroppedFrames:
                        troubled_frame.append(frameINX)
                        droppedFrames = self.w.nDroppedFrames

                    if frameINX == 0:
                        if self.MODE != 'PREVIEW':
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
                
                while self.controller.currentProcess is self and self.controller.end == False:
                    frameINX = 0

                    droppedFrames = self.w.nDroppedFrames
                    troubled_frame = []
                    self.w.flip(False)
                    self.w.recordFrameIntervals = True
                    self.w.flip(False)


                    while frameINX < len(self.frameSet) and self.controller.currentProcess is self:
                        
                        self.frameSet[frameINX].draw()
                        self.w.flip(False)

                        if droppedFrames != self.w.nDroppedFrames:
                            troubled_frame.append(frameINX)
                            droppedFrames = self.w.nDroppedFrames

                        if frameINX == 0:
                            if self.MODE != 'PREVIEW':
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

            self.w.flip()

            if self.controller.key_list.two_phase_on:
                self.twoPhaseBox.draw()
            self.initFrame.draw()

            if self.strideText is not None:
                self.strideText.draw()

            if self.MODE != "PREVIEW" and self.MODE != "USE":
                self.controller.dialogue.draw()
                self.controller.feedback.draw()
            self.w.flip(False)

            self.eventController.clearEvent()

            if self.sync_mode == "Normal" or self.MODE == "TRAIN":
                break

        if self.MODE != 'PREVIEW':
            while self.controller.currentProcess is self:
                core.wait(0.01)
        else:
            self.change(None)

        self.update()
        
        
    def _checkBlock(self):
        # Check if the current block of stimuli has ended, increment the block index if so
        if self.controller.blockCueINX == []:
            self.controller.currentBlockINX += 1
            return True
        else:
            return False
        
        
def log_frame_drops(subject_name, no_of_frames, dropped_frames, block, index, cue_id):
    """
    Log information about dropped frames during the stimulation process.
    
    Args:
        subject_name (str): The name of the subject.
        no_of_frames (int): The total number of frames in the stimulation process.
        dropped_frames (list): A list of indices of the dropped frames.
        block (int): The current block index of the stimulation process.
        index (int): The current epoch index within the block.
        cue_id (int): The current cue ID.
        
    Returns:
        None
    """
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
