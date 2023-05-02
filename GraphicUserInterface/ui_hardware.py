
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMessageBox
from StimulationSystem.EventController import EventController
import numpy as np
import time
import threading
from screeninfo import get_monitors
import win32api

class HardwareManager:
    """
    HardwareManager class is responsible for managing hardware configurations and settings.
    """
    def __init__(self):
        """
        Initializes HardwareManager class with default configurations.
        """
        self.acquisitionSys = []
        self.montage = []
        self.sampleRate = []
        self.streamingIp = []
        self.portNumber = []
        self.remarks = []
        self.COM = []
        self.screenResolution = []
        self.refreshRate = []
        self.stop_event = threading.Event()
        self.chnNUM = 9
        self.chnMontage = ""
        self.monitorIndex = 0

    def renew(self,win):
        """
        Updates the current hardware configuration with the values from the user interface.
        """
        self.acquisitionSys = win.acquisitionSystemComboBox.currentText()
        self.montage = win.montageComboBox.currentText()
        self.sampleRate = int(win.samplingRateHzLineEdit.text())
        self.streamingIp = win.streamingServerLineEdit.text()
        self.portNumber = int(win.portNumberLineEdit.text())
        self.remarks = win.hardware_remark_TextEdit.toPlainText()
        self.COM = win.comParallelPortLineEdit.text()
        
        if win.montageComboBox.currentText() == "9 Channels (OZ O1 O2 POZ PZ PO5 PO6 PO7 PO8)":
            
            self.chnNUM = 9
            self.chnMontage = "OZ O1 O2 POZ PZ PO5 PO6 PO7 PO8"
        else:
            self.chnNUM = 60
            self.chnMontage = "Quick-Cap 64"
        
        self.monitorIndex = win.monitorComboBox.currentIndex()
        
    def reverse_renew(self,win):
        """
        Updates the user interface with the values from the current hardware configuration.
        """
        win.monitorComboBox.setCurrentIndex(self.monitorIndex)
        win.acquisitionSystemComboBox.setCurrentText(self.acquisitionSys)
        win.montageComboBox.setCurrentText(self.montage)
        win.samplingRateHzLineEdit.setText(str(self.sampleRate))
        win.streamingServerLineEdit.setText(self.streamingIp)
        win.portNumberLineEdit.setText(str(self.portNumber))
        win.hardware_remark_TextEdit.setPlainText(self.remarks)
        self.COM = win.comParallelPortLineEdit.setText(self.COM)
        
        if self.chnNUM == 9:
            win.montageComboBox.setCurrentText("9 Channels (OZ O1 O2 POZ PZ PO5 PO6 PO7 PO8)")
        else:
            win.montageComboBox.setCurrentText("60 Channels")
            
    def load_data(self,mgr, win):
        """
        Loads the hardware configuration data from another HardwareManager instance.

        Args:
            mgr (HardwareManager): The source HardwareManager instance.
            win (QWidget): The hardware configuration window.
        """
        self.acquisitionSys = mgr.acquisitionSys
        self.montage = mgr.montage
        self.sampleRate =mgr.sampleRate
        self.streamingIp = mgr.streamingIp
        self.portNumber = mgr.portNumber
        self.remarks =mgr.remarks
        self.COM = mgr.COM 
        
        self.stop_event = threading.Event()
        self.chnNUM =mgr.chnNUM
        self.chnMontage = mgr.chnMontage
        self.reverse_renew(win)
        
        
    
def UI_init(win):
    """
    Initializes the user interface for the hardware configuration window.

    Args:
        win (QWidget): The hardware configuration window.
    """
    win.hardware_manager.stop_event = threading.Event()
    
    # Set the validator to port numbers
    validator = QIntValidator(0, 9999, win.portNumberLineEdit)
    win.portNumberLineEdit.setValidator(validator)
    
    # Set the validator to sampling rate
    validator = QIntValidator(0, 10000, win.samplingRateHzLineEdit)
    win.samplingRateHzLineEdit.setValidator(validator)
    
    
    # Renew values
    win.hardware_manager.renew(win)
    win.triggerTestButton.clicked.connect(lambda: comTest(win))
    win.triggerStopTestButton.clicked.connect(lambda: comStopTest(win))
    
    for index, monitor in enumerate(get_monitors()):
        # Append the screen resolution
        win.hardware_manager.screenResolution.append(f"{monitor.width}x{monitor.height}")
        
        # Append the monitor's refresh rate
        refresh_rate = get_monitor_refresh_rate(index)
        win.hardware_manager.refreshRate.append(refresh_rate)
        
        # Add the monitor to the combo box
        if index == 0:
            win.monitorComboBox.addItem(f"Monitor {index} (Main window)")
            index_ = index
        else:
            win.monitorComboBox.addItem(f"Monitor {index} (Secondary window)")
            index_ = index
            
    
    # Connect the on_monitor_selection_changed function to the combo box
    win.monitorComboBox.currentIndexChanged.connect(lambda: on_monitor_selection_changed(win))
    
    # Call the on_monitor_selection_changed function initially
    on_monitor_selection_changed(win)
        

def on_monitor_selection_changed(win):
    """
    Updates the screen resolution and refresh rate fields in the hardware configuration window based on the selected monitor.
    """
    win.hardware_manager.monitorIndex= win.monitorComboBox.currentIndex()
    win.screenResolutionsLineEdit.setText(win.hardware_manager.screenResolution[win.hardware_manager.monitorIndex])
    win.refreshRateLineEdit.setText(str(win.hardware_manager.refreshRate[win.hardware_manager.monitorIndex]))


def get_monitor_refresh_rate(index):
    """
    Retrieves the refresh rate of the specified monitor.

    Args:
        index (int): The index of the monitor.

    Returns:
        int: The refresh rate of the monitor.
    """
    device = win32api.EnumDisplayDevices(None, index)
    settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
    return settings.DisplayFrequency 
    

def comTestRun(progress_manager, stop_event, COM_no):
    """
    Performs a COM test with the given COM_no and updates the progress_manager accordingly.

    Args:
        progress_manager (dict): A dictionary that is to reflect the progress of the test on UI.
        stop_event (threading.Event): A threading event used to stop the test.
        COM_no (str): The COM number to be tested.
    """
    progress_manager["text"] = "Running com test..."
    # run the com test
    s = [i+1 for i in range(160)]
    np.random.shuffle(s)
    e = EventController(COM=COM_no)
    
    total_iterations = 3 * len(s)
    current_iteration = 0

    for j in range(3):
        for inx,i in enumerate(s):
            print('send %s: [%s]' %(inx,i))
            e.sendEvent(i)  
            time.sleep(0.5)
            e.clearEvent()
            
            current_iteration += 1
            progress_manager["value"] = int((current_iteration / total_iterations) * 100)

            # e.clearEvent()
            if (inx+1)%5==0:
                time.sleep(1)
        
            if stop_event.is_set():
                return
    
def comTest(win):
    """
    Starts the COM test process.
    """
    if win.process_manager.run_blocking == True:
        
        # 阻塞主线程，弹出提示对话框
        message_box = QMessageBox()
        message_box.setText("Please wait until the running process is complete.")
        message_box.exec_()
        
    else:
        if win.com_trigger_process == None:
            win.hardware_manager.renew(win)
            win.com_trigger_process = threading.Thread(target=comTestRun, args=(win.process_manager.progress_manager, win.hardware_manager.stop_event, win.hardware_manager.COM), name = "comTestProcess")
            win.com_trigger_process.start()
            # comTestRun(win.process_manager.progress_manager)
            win.process_manager.run_blocking = True

def comStopTest(win):
    """
    Stops the COM test process.
    """
    if win.com_trigger_process != None:
        win.hardware_manager.stop_event.set()
        win.com_trigger_process.join()
        win.hardware_manager.stop_event = threading.Event()  
        win.process_manager.run_blocking = False
        win.com_trigger_process = None
        win.process_manager.progress_manager["text"] = "Process Stopped."
        win.process_manager.progress_manager["value"] = 101
        
    else:
        # 阻塞主线程，弹出提示对话框
        message_box = QMessageBox()
        message_box.setText("Please run the com test first.")
        message_box.exec_()
        