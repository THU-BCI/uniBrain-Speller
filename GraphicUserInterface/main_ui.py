# Append the current directory to the system path
import sys
sys.path.append('.')

# Import necessary libraries
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
import os
import pathlib
import pickle
import multiprocessing
from CommonSystem.Config import Config
from multi_process_worker import operation_worker, stimulation_worker
from make_a_report import create_pdf_main
from ui_StimulusControl import flickering_on_complete

# Load the UI file
form_class = uic.loadUiType("GraphicUserInterface/main.ui")[0]

# Import custom libraries
import ui_keyboard as key
import ui_user as user
import ui_hardware as hw
import ui_processing as proc

class mainWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        
        # Set up the user interface by calling the setupUi method of the form_class
        self.setupUi(self)
        
        self.stimulator = None
        self.operation_messenager_process = None
        self.stimulation_messenger_process = None
        self.com_trigger_process = None
        self.MULTIPROCESS_RUN_START = False
        self.PROCESS_WAIT_FOR_FINISH = False
        
        # other initialization
        self.config = Config()
        
        # Initialize the UI elements for the keyboard and user interface
        self.UI_init()
        self.user_manager = user.UserManager()
        user.UI_init(self)
        self.hardware_manager = hw.HardwareManager()
        hw.UI_init(self)
        self.keyboard_manager = key.KeyboardManager()
        key.UI_init(self)
        self.process_manager = proc.ProcessManager()
        proc.UI_init(self)
        self.retrain_model_threads = []

        # Create QTimer objects
        self.init_timers()
        

    def init_timers(self):
        # Timer for progress bar
        self.timer_progress = QTimer(self)
        self.timer_progress.setInterval(250)
        self.timer_progress.timeout.connect(lambda: self.handle_timer_event(self.process_manager.progress_manager["value"],self.process_manager.progress_manager["text"]))

        # Timer for operation
        self.timer_operation = QTimer(self)
        self.timer_operation.setInterval(1000)
        self.timer_operation.timeout.connect(self.operation_timer_event)

        # Timer for table refresh
        self.table_refresh_operation = QTimer(self)
        self.table_refresh_operation.setInterval(750)
        self.table_refresh_operation.timeout.connect(lambda: proc.refresh_key_count_accross_multiprocessing(self, self.process_manager.progress_manager["output_count"]))

        # Start timers
        self.timer_progress.start()
        self.timer_operation.start()
        self.table_refresh_operation.start()
        
    def operation_timer_event(self):
        
        if self.MULTIPROCESS_RUN_START == True:
            
            self.MULTIPROCESS_RUN_START = False
            self.PROCESS_WAIT_FOR_FINISH = True
            
            if self.process_manager.run_mode != "PREVIEW":
                
                if __name__ == '__main__':
                    
                    self.process_manager.mtd_manager[self.config.feature_algo].start_timer()
                    self.operation_messenager_process = multiprocessing.Process(target=operation_worker, args=(self.config,self.process_manager.progress_manager,), name = "OperationProcess")
                    self.stimulation_messenger_process = multiprocessing.Process(target=stimulation_worker, args=(self.config,self.process_manager.progress_manager,), name = "StimulationProcess")
                    self.operation_messenager_process.start()
                    self.stimulation_messenger_process.start()
                    
            else: # preview mode
                
                if __name__ == '__main__':
                    
                    self.stimulation_messenger_process = multiprocessing.Process(target=stimulation_worker, args=(self.config,self.process_manager.progress_manager,), name = "StimulationProcess")
                    self.stimulation_messenger_process.start()
                                
        if self.PROCESS_WAIT_FOR_FINISH == True:
            # Check if the child processes are still running
            if not self.stimulation_messenger_process.is_alive():
                
                if self.process_manager.run_mode != "PREVIEW":
                    if not self.operation_messenager_process.is_alive():
                        self.PROCESS_WAIT_FOR_FINISH = False
                        self.process_manager.mtd_manager[self.config.feature_algo].stop_timer()
                        self.operation_messenager_process.join()
                        self.stimulation_messenger_process.join()
                        # Both child processes have finished, so break out of the loop
                        flickering_on_complete(self)
                        self.process_manager.refresh_calculation(self, refresh_config = False)
                        create_pdf_main(self)
                else: # preview mode
                    self.PROCESS_WAIT_FOR_FINISH = False
                    self.stimulation_messenger_process.join()
                    # Both child processes have finished, so break out of the loop
                    flickering_on_complete(self)

    def UI_init(self):
        
        self.state_horizontal_tab.setStyleSheet('''
        QTabWidget::tab-bar {
            alignment: center;
        }''')
        self.actionLoad.triggered.connect(self.file_load)
        self.actionSave_As.triggered.connect(self.file_new_save)
        self.actionSave.triggered.connect(self.file_save)
        self.save_info_button.clicked.connect(self.file_save)
        
        user_tab_image = QIcon(os.path.join("GraphicUserInterface","images","user.png"))
        keyboard_tab_image = QIcon(os.path.join("GraphicUserInterface","images","keyboard.png"))
        hardware_tab_image = QIcon(os.path.join("GraphicUserInterface","images","hardware.png"))
        process_tab_image = QIcon(os.path.join("GraphicUserInterface","images","processing.png"))
        
        # Set the icons for each tab
        self.state_horizontal_tab.setTabIcon(0, user_tab_image)
        self.state_horizontal_tab.setTabIcon(1, keyboard_tab_image)
        self.state_horizontal_tab.setTabIcon(2, hardware_tab_image)
        self.state_horizontal_tab.setTabIcon(3, process_tab_image)
        
    def handle_timer_event(self, value, text):
        
        self.progressBar_label.setText(text)
        self.progressBar.setValue(int(value))
        if value > 100 or value == 0:
            self.progressBar.setVisible(False)
        else:
            self.progressBar.setVisible(True)
            
        if self.keyboard_manager.current_key_list.current_thread is not None:
            if not self.keyboard_manager.current_key_list.current_thread.is_alive():
                
                self.mouseStrideLengthLineEdit.setText(str(self.keyboard_manager.current_key_list.stride))
                self.strideStepLineEdit.setText(str(self.keyboard_manager.current_key_list.strideStep))
                self.stimulusLengthLineEdit.setText(str(self.keyboard_manager.current_key_list.stim_time))
                
                self.keyboard_manager.current_key_list.current_thread = None
                
        self.other_work()
        
    def other_work(self):
        
        # other works
        self.process_manager.mtd_manager[self.process_manager.feature_extraction].reflect_timer()
        self.process_manager.mtd_manager[self.process_manager.feature_extraction].reflectUI(self)
        pass
        
    # Override the resize_event method to adjust the size of the keyboard preview and frequency preview images
    def resizeEvent(self, event):

        # Get the new width of the main window
        new_width = event.size().width() - 90

        self.verticalFrame_2.setMinimumWidth(new_width)
        # Set the maximum width of the target widget to the new width
        self.verticalFrame_2.setMaximumWidth(new_width)
        
        # Keep the aspect ratio of the images in the preview panels
        
        key.adjust_picture_size(self,new_width)
            
        # resize the columns width
        column_width = int(event.size().width()/12)
        for i in range(self.keyboard_table.columnCount()):
            self.keyboard_table.setColumnWidth(i, column_width)
            
        # resize the columns width
        column_width = int(event.size().width()/9.8)
        for i in range(self.keyboard_processing_table.columnCount()):
            self.keyboard_processing_table.setColumnWidth(i, column_width)
            
            
        self.state_horizontal_frame.setMinimumHeight(int(self.size().height()*0.68))
        self.state_horizontal_frame.setMaximumHeight(int(self.size().height()*0.78))
        
        self.centralwidget.setMinimumWidth(int(self.size().width()*0.99))
        self.centralwidget.setMaximumWidth(int(self.size().width()*0.99))
    
    
        self.state_horizontal_frame.setMinimumWidth(int(self.size().width()*0.98))
        self.state_horizontal_frame.setMaximumWidth(int(self.size().width()*0.98))
        self.state_horizontal_tab.setMinimumWidth(int(self.size().width()*0.92))
        self.state_horizontal_tab.setMaximumWidth(int(self.size().width()*0.92))
        self.scrollAreaWidgetContents.setMaximumWidth(int(self.state_horizontal_tab.width()*0.95)) # keyboard table size
        self.verticalFrame_2.setMaximumWidth(int(self.state_horizontal_tab.width()*0.95)) # keyboard table size
        self.state_horizontal_tab.setMinimumHeight(int(self.state_horizontal_frame.height()*0.95))
        self.state_horizontal_tab.setMaximumHeight(int(self.state_horizontal_frame.height()*0.95))
    
    def my_save(self, file_path):
        
        self.process_manager.progress_manager["text"] = "Saving..."
        self.handle_timer_event(self.process_manager.progress_manager["value"],self.process_manager.progress_manager["text"])
        
        self.renew_all()
        
        
        count = self.process_manager.progress_manager["output_count"]
        self.hardware_manager.stop_event = None # because it is not serializable
        self.process_manager.progress_manager = None # because it is not serializable
        
        # Create a dictionary with user and keyboard managers as values
        data = {"user_manager": self.user_manager, "keyboard_manager": self.keyboard_manager, 
                "hardware_manager": self.hardware_manager, "process_manager": self.process_manager}
        
        with open(file_path, "wb") as file:
            pickle.dump(data, file)
            # pickle.dump(data, file)
            
        import threading
        self.hardware_manager.stop_event = threading.Event() # because it is not serializable
        self.process_manager.progress_manager_reset(count) # because it is not serializable
        self.process_manager.progress_manager["text"] = "File Saved!"
        

    def my_load(self, fname):
        self.process_manager.progress_manager["text"] = "File Loading..."
        self.handle_timer_event(self.process_manager.progress_manager["value"],self.process_manager.progress_manager["text"])
        
        if os.path.exists(fname):
            with open(fname, 'rb') as file:
                data = pickle.load(file) 
        else:
            print(f"File not found: {fname}")
            return
        
            
        # Set the loaded objects to the window's user manager and keyboard manager attributes
        
        self.user_manager.load_data(data["user_manager"],fname,self)
        self.keyboard_manager.load_data(data["keyboard_manager"],self)
        self.hardware_manager.load_data(data["hardware_manager"],self)
        self.process_manager.load_data(data["process_manager"],self)
        
        self.process_manager.progress_manager["text"] = "File Loaded!"
        
    
    def file_load(self):
        
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',
                                            str(pathlib.Path().absolute()) + os.sep, "SSVEP program files (*.ssvep)")
        
        if not fname[0] == '':
            
            self.user_manager.makeUser(fname[0])
            self.my_load(fname[0])
            user.renew_Current_Image(self)
            

    def file_save(self):
        
        if not self.user_manager.save_path == None:

            self.my_save(self.user_manager.save_path)
            
        else:
            
            self.file_new_save()
            
        
    def file_new_save(self):
        
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', 
                                                        str(pathlib.Path().absolute()) + os.sep,"SSVEP program files (*.ssvep)")
        
        if not fname[0] == '':
            
            # **edit make make user
            self.user_manager.makeUser(fname[0])
                
            self.my_save(fname[0])
    
    def renew_all(self):
        
        self.user_manager.current_user.renew(self)
        
        # renew data
        self.hardware_manager.renew(self)
        self.process_manager.renew(self)
        self.keyboard_manager.renew(self)
        self.user_manager.current_user.renew(self)    

        
if __name__ == "__main__":
    
    # Create the application and show the form
    app = QtWidgets.QApplication([])
    win = mainWindow()
    win.show()

    # Execute the event loop of the application
    app.exec_()
