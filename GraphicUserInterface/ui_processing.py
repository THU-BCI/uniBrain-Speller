import os
import time
import pandas as pd
import numpy as np
import multiprocessing
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QAbstractItemView
from PyQt5.QtGui import QFontMetrics, QIntValidator, QDoubleValidator
from PyQt5.QtCore import QThread
from CommonSystem.Config import config_make_file
import json
from make_a_report import create_pdf_main
import ui_StimulusControl

class ProcessManager:
    def __init__(self):
        self.feature_extraction = []
        self.win_length = 1.0
        self.run_mode = []  # PREVIEW, TRAIN, TEST, USE
        self.num_of_blocks = []
        self.sync_mode = "Normal"
        self.run_blocking = False  # control from ui_StimulusControl.py
        self.progress_manager = multiprocessing.Manager().dict()
        self.progress_manager["value"] = 0
        self.progress_manager["text"] = ""
        self.progress_manager["output_count"] = 0
        self.p_value = 0.01
        self.mtd_manager = {}
        relative_folder_path = "Result"
        full_path = os.path.abspath(relative_folder_path)
        if not os.path.exists(relative_folder_path):
            os.makedirs(relative_folder_path)
        self.data_saved_path  = full_path
        
    def renew(self, win):
        """
        Update values from the UI.

        Args:
            win: The main window instance.
        """
        current_text = win.feature_extraction_combo_box.currentText()
        if current_text == "TRCA (training required)":
            self.feature_extraction = "TRCA"
        elif current_text == "FBCCA (training free)":
            self.feature_extraction = "FBCCA"

        if win.process_manager.progress_manager is None:
            win.process_manager.progress_manager_reset(0)

        win.process_manager.refresh_progress_key_count(win.keyboard_manager.current_key_list.keys)

        self.win_length = float(win.window_length_line_edit.text())
        self.num_of_blocks = int(win.number_of_blocks_line_edit.text())
        self.p_value = float(win.p_value_line_edit.text())
        self.data_saved_path = win.data_save_path_line_edit.text()

        self.mtd_manager["TRCA"].stop_timer()
        self.mtd_manager["FBCCA"].stop_timer()
        
    def load_data(self,mgr,win):
        """
        Load data from file.

        Args:
            mgr: The manager object to load data from.
            win: The main window instance.
        """
        self.feature_extraction = mgr.feature_extraction
        self.win_length = mgr.win_length
        self.run_mode = "TRAIN"
        self.num_of_blocks = mgr.num_of_blocks
        self.sync_mode = mgr.sync_mode
        self.run_blocking = False  # control from ui_StimulusControl.py
        self.progress_manager = multiprocessing.Manager().dict()
        self.progress_manager["value"] = 0
        self.progress_manager["text"] = ""
        self.progress_manager["output_count"] = 0
        self.p_value = mgr.p_value
        self.mtd_manager = mgr.mtd_manager
        
        if os.path.exists(mgr.data_saved_path ):
            self.data_saved_path  = mgr.data_saved_path 
        else:
            relative_folder_path = "Result"
            full_path = os.path.abspath(relative_folder_path)
            
            # Ensure the folder exists
            if not os.path.exists(relative_folder_path):
                os.makedirs(relative_folder_path)
            self.data_saved_path  = full_path
        self.reverse_renew(win)
        
    def reverse_renew(self,win):
        """
        Update the UI with values.

        Args:
            win: The main window instance.
        """
        if self.feature_extraction == "TRCA":
            win.feature_extraction_combo_box.setCurrentText("TRCA (training required)")
        elif self.feature_extraction == "FBCCA":
            win.feature_extraction_combo_box.setCurrentText("FBCCA (training not required)")
        
        if self.sync_mode == "Normal":
            win.sync_combo_box.setCurrentText("Normal")
        elif self.sync_mode == "DW":
            win.sync_combo_box.setCurrentText("Dynamic Window")
        elif self.sync_mode == "NP":
            win.sync_combo_box.setCurrentText("Normal with p-Value")
        
        win.window_length_line_edit.setText("{:.1f}".format(self.win_length))
        win.number_of_blocks_line_edit.setText(str(self.num_of_blocks))
        win.p_value_line_edit.setText(str(self.p_value))
        win.data_save_path_line_edit.setText(win.process_manager.data_saved_path )
        
        set_radio_button_state(win)
        self.refresh_calculation(win,refresh_config = True, message_box = False)
        
    def progress_manager_reset(self, count):
        """
        Reset progress manager values.

        Args:
            count: The count of output keys.
        """
        self.progress_manager = multiprocessing.Manager().dict()
        self.progress_manager["value"] = 0
        self.progress_manager["text"] = ""
        self.progress_manager["output_count"] = count
        
    def refresh_calculation(self, win, refresh_config = True, message_box = True):
        """
        Recalculate accuracies and update the UI.

        Args:
            win: The main window instance.
            refresh_config: Whether to refresh the configuration.
            message_box: Whether to show the message box.
        """
        if self.run_blocking == False:

            if refresh_config:
                win.renew_all()
                config_make_file(win)

            # Train accuracies
            directory = os.path.join(win.config.resultPath, win.config.personName, "record")
            filtered_files = get_filtered_files(directory, win.config.prefix, "offline.csv")
            
            if not filtered_files:
                if message_box:
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("Warning")
                    msg_box.setText("Please train some blocks first!")
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.exec_()

                for i in range(len(win.keyboard_manager.current_key_list.keys)):
                    win.keyboard_manager.current_key_list.keys[i].trainAcc = None

                mean_accuracy = None
                mean_itr = None

            else:
                frames = load_data_frames(filtered_files, directory)
                mean_accuracy, mean_itr = calculate_mean_accuracy_and_itr(frames, win)
                filtered_rows = frames[frames['Window Length'] == win.config.winLEN]

                if not filtered_rows.empty:
                    update_train_accuracies(filtered_rows, win)
                else:
                    for i in range(len(win.keyboard_manager.current_key_list.keys)):
                        win.keyboard_manager.current_key_list.keys[i].trainAcc = None

            self.mtd_manager[win.config.feature_algo].accuracy = mean_accuracy
            self.mtd_manager[win.config.feature_algo].ITR = mean_itr

            # Test accuracies
            directory = os.path.join(win.config.resultPath, win.config.personName, "record")
            filtered_files = get_filtered_files(directory, win.config.prefix, "trackEpoch.csv")

            if filtered_files:
                frames = load_data_frames(filtered_files, directory)
                update_test_accuracies(frames, win)
            else:
                for i in range(len(win.keyboard_manager.current_key_list.keys)):
                    win.keyboard_manager.current_key_list.keys[i].testAcc = None

            load_prc_table_with_key(win, win.keyboard_manager.current_key_list)
            check_model(win)

        else:
            # If the main thread is blocked, display a message box
            message_box = QMessageBox()
            message_box.setText("Please wait until the process is complete.")
            message_box.exec_()

    
    def refresh_progress_key_count(self, keys):
        """
        Update the output_count in the progress_manager.

        Args:
            keys: List of keys for which to count outputs.
        """
        key_outputs = [key.output for key in keys]
        self.progress_manager["output_count"] = key_outputs
        
def UI_init(win):
    
    """Initialize the UI."""
    set_validators(win)
    set_initial_text(win)
    connect_signals(win)
    initialize_method_manager(win)
    sync_comboBox_changed(win)
    run_radio_button_clicked(win)
    load_prc_table_with_key(win, win.keyboard_manager.current_key_list)
    config_make_file(win)
    check_model(win)


def set_validators(win):
    """Set the validators for input fields."""
    validator = QIntValidator(0, 10, win.number_of_blocks_line_edit)
    win.number_of_blocks_line_edit.setValidator(validator)
    double_validator = QDoubleValidator(0.3, 10, 1)
    win.window_length_line_edit.setValidator(double_validator)


def set_initial_text(win):
    """Set the initial text for input fields."""
    win.data_save_path_line_edit.setText(win.process_manager.data_saved_path)


def connect_signals(win):
    """Connect signals and slots for UI elements."""
    win.trainRadioButton.clicked.connect(lambda: run_radio_button_clicked(win))
    win.testRadioButton.clicked.connect(lambda: run_radio_button_clicked(win))
    win.useRadioButton.clicked.connect(lambda: run_radio_button_clicked(win))
    win.debugRadioButton.clicked.connect(lambda: run_radio_button_clicked(win))
    win.sync_combo_box.currentIndexChanged.connect(lambda: sync_comboBox_changed(win))
    win.setDataSavePathButton.clicked.connect(lambda: on_line_edit_click(win))
    win.runNowButton.clicked.connect(lambda: run_button_clicked(win))
    win.feature_extraction_combo_box.currentIndexChanged.connect(lambda: FE_method_changed(win))
    win.clearHistoryPushButton.clicked.connect(lambda: clear_history(win))
    win.retrainModelPushButton.clicked.connect(lambda: start_retrain_model_thread(win))
    win.refreshCalculationPushButton.clicked.connect(lambda: win.process_manager.refresh_calculation(win))
    win.keyboard_processing_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

def set_radio_button_state(win):
    """Set the state of the radio buttons according to the run mode."""
    if win.process_manager.run_mode == "TRAIN":
        win.trainRadioButton.setChecked(True)
        win.number_of_blocks_line_edit.setEnabled(True)
    elif win.process_manager.run_mode == "TEST":
        win.testRadioButton.setChecked(True)
        win.number_of_blocks_line_edit.setEnabled(True)
    elif win.process_manager.run_mode == "USE":
        win.useRadioButton.setChecked(True)
        win.number_of_blocks_line_edit.setEnabled(False)
    else:
        win.debugRadioButton.setChecked(True)
        win.number_of_blocks_line_edit.setEnabled(True)

def initialize_method_manager(win):
    """Initialize the method manager with available methods."""
    for i in range(win.feature_extraction_combo_box.count()):
        item_text = win.feature_extraction_combo_box.itemText(i)
        if item_text == "TRCA (training required)":
            win.process_manager.mtd_manager["TRCA"] = method("TRCA")
        elif item_text == "FBCCA (training free)":
            win.process_manager.mtd_manager["FBCCA"] = method("FBCCA")
    win.process_manager.renew(win)
    
def check_model(win):
    """
    Check if the model is trained or not.

    Args:
        win: The main window instance.
    """
    file_name = f'{win.config.prefix}Model.pkl'
    savepath = os.path.join(win.config.resultPath, win.config.personName)

    file_path = os.path.join(savepath, 'models', file_name)
    json_path = os.path.splitext(file_path)[0] + ".json"

    if os.path.exists(file_path):
        update_ui_model_info(win, json_path, file_name)
    else:
        set_ui_model_not_ready(win)

def update_ui_model_info(win, json_path, file_name):
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        win.blockNumberLineEdit.setText(str(data["block_count"]))
        win.modelExistsLineEdit.setText("Ready")
        win.modelExistsLineEdit.setStyleSheet("color: green;")
    else:
        show_missing_json_warning(file_name)
        set_ui_model_not_ready(win)

def show_missing_json_warning(file_name):
    msg_box = QMessageBox()
    msg_box.setText(f"The JSON file for the model '{file_name}' is missing.")
    msg_box.exec_()

def set_ui_model_not_ready(win):
    win.blockNumberLineEdit.setText("0")
    win.modelExistsLineEdit.setText("Not Ready")
    win.modelExistsLineEdit.setStyleSheet("color: red;")

def refresh_key_count_accross_multiprocessing(win, key_counts):
    """
    Refresh key count across multiprocessing.

    Args:
        win: The main window instance.
        key_counts: The list of key counts.
    """
    for key_list in win.keyboard_manager.key_lists:
        if key_list.name == win.config.keyType:
            for key_list_key, key_count in zip(key_list.keys, key_counts):
                key_list_key.output = key_count
        
class method:
    
    def __init__(self, name=""):
        self.name = name
        self.total_output = 0
        self.accuracy = None
        self.ITR = None
        self.time_online = 0
        self.on_timer = None
    
    def reflectUI(self, win):
        """Update the UI with the current method's data."""
        win.method_name_label.setText(self.name) 
        if self.accuracy== None:
            win.total_accuracy_label.setText("N/A") 
        else:
            win.total_accuracy_label.setText(str(round(self.accuracy*100))+"%") 
            
        if self.ITR== None:
            win.last_ITR_label.setText("N/A") 
        else:
            win.last_ITR_label.setText(str(round(self.ITR))) 
            
        # Convert accumulated time to hours, minutes, and seconds
        hours, remainder = divmod(self.time_online, 3600)
        minutes, seconds = divmod(remainder, 60)
        # Format and display the accumulated time string
        accumulated_time_str = f"{int(hours)}H {int(minutes)}M\n{int(seconds)}S"

        win.total_time_label.setText(accumulated_time_str)
        
        
        # Get the font metrics of the label
        font_metrics = QFontMetrics(win.total_time_label.font())

        # Calculate the width required to display the time string
        text_width = font_metrics.width(accumulated_time_str)

        # Add some extra padding to accommodate any changes in the text
        padding = 10

        # Set the minimum width of the label
        win.total_time_label.setMinimumWidth(text_width + padding)
        
        self.refresh_table_output_column(win)
        win.total_output_label.setText(str(self.total_output)) 
        
        
    def start_timer(self):
        self.on_timer = time.time()

    def reflect_timer(self):
        if self.on_timer != None:
            elapsed_time  = time.time() - self.on_timer
            self.on_timer = time.time()
            self.time_online += elapsed_time
            
    def stop_timer(self):
        self.on_timer = None
    
    def refresh_table_output_column(self,win):
        column_index = 5  # "No of\nOutputs" 列的索引
        total_output_ = 0        
        for i, key in enumerate(win.keyboard_manager.current_key_list.keys):
            # Create a QTableWidgetItem for the new output count
            output = QtWidgets.QTableWidgetItem(str(key.output))

            # Set widget properties
            output.setTextAlignment(QtCore.Qt.AlignCenter)
            
            # accumulate output count
            total_output_ += key.output
            
            # Update the item in the table
            win.keyboard_processing_table.setItem(i, column_index, output)
            
        self.total_output = total_output_
        pass
        
    
        
def FE_method_changed(win):
    """Update the feature extraction method based on the selected option."""
    if win.feature_extraction_combo_box.currentText() == "TRCA (training required)":
        win.process_manager.feature_extraction = "TRCA"
    elif win.feature_extraction_combo_box.currentText() == "FBCCA (training free)":
        win.process_manager.feature_extraction = "FBCCA"

    win.process_manager.refresh_calculation(win, refresh_config=True, message_box=False)
       


class RetrainModelThread(QThread):
    def __init__(self, win, progress_manager):
        super().__init__()
        self.win = win
        self.progress_manager = progress_manager

    def run(self):
        retrain_model_click_function(self.win, self.progress_manager)


def start_retrain_model_thread(win):
    progress_manager = win.process_manager.progress_manager
    retrain_model_thread = RetrainModelThread(win, progress_manager)
    win.retrain_model_threads.append(retrain_model_thread)
    retrain_model_thread.finished.connect(lambda: win.retrain_model_threads.remove(retrain_model_thread))
    retrain_model_thread.start()
    
def retrain_model_click_function(win, progress_manager, refresh_config=True):
    """
    Retrain the model with the available training data.

    Args:
        win: An instance of the main window that contains configurations.
        progress_manager: An instance of the progress manager.
        refresh_config: A boolean value to decide if the configuration should be refreshed.

    Returns:
        None.
    """
    
    # Block the process if another process is running
    if win.process_manager.run_blocking:
        message_box = QMessageBox()
        message_box.setText("Please wait until the process is complete.")
        message_box.exec_()
        return

    # Refresh configurations if required
    if refresh_config:
        win.renew_all()
        config_make_file(win)

    win.config.MODE = "TRAIN"

    # Check for the existence of a directory containing data
    directory = os.path.join(win.config.resultPath, win.config.personName, "data")
    if os.path.exists(directory):
        all_files = os.listdir(directory)
        prefix = win.config.prefix.replace(win.config.feature_algo+"_", "")
        filtered_files = [file for file in all_files if file.startswith(prefix) and file.endswith("train.pkl") and not file.endswith("use.pkl")]
    else:
        message_box = QMessageBox()
        message_box.setText("There is no directory available. Please do some training first.")
        message_box.exec_()
        return

    # Check for the existence of data files in the directory
    if not filtered_files:
        message_box = QMessageBox()
        message_box.setText("There is no data available. Please do some training first.")
        message_box.exec_()
        return

    import pickle

    trainX = None
    trainy = None
    required_length = (win.config.winLEN) * win.config.srate
    required_channel = win.config.chnNUM

    # Load and process the data
    for filename in filtered_files:
        path = os.path.join(directory, filename)

        with open(path, "rb") as fp:
            data = pickle.load(fp)

        data_X = np.squeeze(data['X'])
        data_y = np.squeeze(data['y'])

        # Check if the data meets the requirements
        if data_X.shape[1] == required_channel and data_X.shape[2] >= required_length:
            if trainX is None:
                trainX = np.squeeze(data_X)
                trainy = np.squeeze(data_y)
                shortest_time = trainX.shape[-1]
            else:
                # Compare the lengths of data_X and trainX
                min_length = min(data_X.shape[-1], trainX.shape[-1])

                # Trim the longer one to match the length of the shorter one
                data_X = data_X[:, :, :min_length]
                trainX = trainX[:, :, :min_length]

                # Update the shortest_time variable with the new minimum length
                shortest_time = min_length

                # Concatenate the data
                trainX = np.concatenate((trainX, data_X), axis=0)
                trainy = np.concatenate((trainy, data_y), axis=0)

    # Check if there is any suitable data
    if trainX is None:
        message_box = QMessageBox()
        message_box.setText("There is no suitable data. Please do some training first.")
        message_box.exec_()
        return

    from OperationSystem.AnalysisProcess.TestingProcess import TestingProcess
    from OperationSystem.AnalysisProcess.TrainingProcess import TrainingProcess

    # Create a TrainingProcess instance
    prc = TrainingProcess()

    class Controller:
        def __init__(self):
            self.trainData = {
                'X': None,
                'y': None
            }
            self.testing_process = None

    prc.controller = Controller()
    prc.controller.testing_process = TestingProcess()
    prc.targetNUM = win.config.targetNUM

    # Set up the training process configuration
    prc.winLEN = win.config.winLEN
    prc.srate = win.config.srate
    prc.frequency = win.config.frequency
    prc.phase = win.config.phase
    prc.lag = win.config.lag

    
    # Adjust the window length if necessary
    if prc.winLEN > (shortest_time/prc.srate - prc.lag):
        prc.winLEN = (shortest_time/prc.srate - prc.lag)
        win.process_manager.win_length = round(prc.winLEN, 1)
        win.process_manager.reverse_renew(win)

    prc.n_band = win.config.n_band
    prc.feature_algo = win.config.feature_algo
    prc.controller.trainData['X'] = trainX
    prc.controller.trainData['y'] = trainy
    prc.controller.currentBlockINX = int(trainX.shape[0]/win.config.targetNUM)
    prc.progress_manager = progress_manager
    prc.p_value = win.config.p_value
    prc.sync_mode = "Normal"
    prc.prefix = win.config.prefix
    prc.prefix_with_time = win.config.prefix_with_time
    prc.savepath = os.path.join(win.config.resultPath, win.config.personName)
    prc.personName = win.config.personName
    prc.paradigm = win.config.paradigm

    # Train the model
    prc.trainModel()

    # Evaluate the model performance
    prc.performance(prc.controller.trainData['X'], prc.controller.trainData['y'])

    # Visualize the results
    prc.viz()

    win.config.blockNUM = int(trainX.shape[0]/win.config.targetNUM)

    # Refresh calculation and create a PDF report
    win.process_manager.refresh_calculation(win, refresh_config=False)
    create_pdf_main(win)
    
    # Renew progress text
    win.process_manager.progress_manager["text"] = "Model retrain done."

    
def on_line_edit_click(win):
    file_name = QFileDialog.getExistingDirectory(win, "Select Directory")

    if file_name:
        win.data_save_path_line_edit.setText(file_name)
        win.process_manager.data_saved_path  = file_name

def sync_comboBox_changed(win):
    # win.keyboard_manager.frames_ready = False
    if win.sync_combo_box.currentText() == "Normal":
        win.process_manager.sync_mode = "Normal"
        win.pValueLabel.setEnabled(False)
        win.p_value_line_edit.setEnabled(False)
        win.pValueLabel.hide()
        win.p_value_line_edit.hide()
    elif win.sync_combo_box.currentText() == "Dynamic Window":
        win.process_manager.sync_mode = "DW"
        win.pValueLabel.setEnabled(True)
        win.p_value_line_edit.setEnabled(True)
        win.pValueLabel.show()
        win.p_value_line_edit.show()
        # trigger click on win.testRadioButton if mode is train
        if win.process_manager.run_mode == "TRAIN":
            win.testRadioButton.click()
    elif win.sync_combo_box.currentText() == "Normal with p-Value":
        win.process_manager.sync_mode = "NP"
        win.pValueLabel.setEnabled(True)
        win.p_value_line_edit.setEnabled(True)
        win.pValueLabel.show()
        win.p_value_line_edit.show()
        # trigger click on win.testRadioButton if mode is train
        if win.process_manager.run_mode == "TRAIN":
            win.testRadioButton.click()
        
    
def run_button_clicked(win):
    if win.process_manager.run_mode == "DEBUG":
        QtWidgets.QMessageBox.warning(win, "Debug Mode Warning", "Debug mode is currently only available for Keyboard 43 keys, debug mode is a combination of Test mode and Use mode. The Keyboard 43 keys will be selected.")
    
    ui_StimulusControl.processing_run(win)
    

def load_prc_table_with_key(win, KeyList):
    """
    Load the keyboard_processing_table with the incoming key array
    """
    win.keyboard_processing_table.clearContents()
    win.keyboard_processing_table.setColumnCount(6)
    
    # set row height to 40
    win.keyboard_processing_table.verticalHeader().setDefaultSectionSize(40)
    
    win.keyboard_processing_table.setHorizontalHeaderLabels( ["Key\nName", "Freq\n(Hz)", "Phase\n(rad)", "Training\nAccuracy (%)", "Testing\nAccuracy (%)", 
                                                              "No of\nOutputs"])
    win.keyboard_processing_table.setRowCount(len(KeyList.keys))
    win.keyboard_processing_table.horizontalHeader().setStyleSheet("QHeaderView::section { border: 2px solid black; }")

    for i, key in enumerate(KeyList.keys): 
        # Create widgets for each cell
        key_name = QtWidgets.QTableWidgetItem(key.key_name)
        frequency = QtWidgets.QTableWidgetItem(str(key.frequency))
        phase = QtWidgets.QTableWidgetItem(str(key.phase))
        
        if key.trainAcc == None:
            trainAcc = QtWidgets.QTableWidgetItem("N/A")
        else:
            trainAcc = QtWidgets.QTableWidgetItem(str(round(key.trainAcc*100,1)))
        if key.testAcc == None:
            testAcc = QtWidgets.QTableWidgetItem("N/A")
        else:
            testAcc = QtWidgets.QTableWidgetItem(str(round(key.testAcc*100,1)))
            
        output = QtWidgets.QTableWidgetItem(str(key.output))
        
        # Set widget properties
        for item in (key_name, frequency, phase, trainAcc, testAcc, output):
            item.setTextAlignment(QtCore.Qt.AlignCenter)
        
        
        win.keyboard_processing_table.setItem(i, 0, key_name)
        win.keyboard_processing_table.setItem(i, 1, frequency)
        win.keyboard_processing_table.setItem(i, 2, phase)
        win.keyboard_processing_table.setItem(i, 3, trainAcc)
        win.keyboard_processing_table.setItem(i, 4, testAcc)
        win.keyboard_processing_table.setItem(i, 5, output)


    
def run_radio_button_clicked(win):
    
    # win.keyboard_manager.frames_ready = False
    
    if win.trainRadioButton.isChecked():
        win.number_of_blocks_line_edit.setEnabled(True)
        win.process_manager.run_mode = "TRAIN"
        win.sync_combo_box.setCurrentText("Normal")
    elif win.testRadioButton.isChecked():
        win.number_of_blocks_line_edit.setEnabled(True)
        win.process_manager.run_mode = "TEST"
    elif win.useRadioButton.isChecked():
        win.number_of_blocks_line_edit.setEnabled(False)
        win.process_manager.run_mode = "USE"
    else:
        win.number_of_blocks_line_edit.setEnabled(True)
        win.process_manager.run_mode = "DEBUG"
        

def clear_history(win):
    
    if win.process_manager.run_blocking == False:
        
        directory = os.path.join(win.config.resultPath, win.config.personName, "record")
        
        if not os.path.exists(directory):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("There's no directory yet.")
            msg.setInformativeText("Please run the program at least once.")
            msg.setWindowTitle("No Directory")
            msg.exec_()
            return

        if not os.listdir(directory):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("There are no files in the directory yet.")
            msg.setInformativeText("Please run the program at least once.")
            msg.setWindowTitle("No Files")
            msg.exec_()
            return

        # Confirm dialog
        confirm_dialog = QDialog()
        confirm_dialog.setWindowTitle("Delete History")
        vbox = QVBoxLayout()

        confirm_label = QLabel("Please backup the data before proceeding. Are you sure you want to delete all history?")
        vbox.addWidget(confirm_label)

        def on_yes_button_clicked():
            # Remove all files in the directory
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {str(e)}")

            confirm_dialog.accept()

        def on_no_button_clicked():
            confirm_dialog.reject()

        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(on_yes_button_clicked)
        vbox.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(on_no_button_clicked)
        vbox.addWidget(no_button)

        confirm_dialog.setLayout(vbox)
        confirm_dialog.exec_()
        
    else:
        
        # 如果需要阻塞主线程，弹出提示对话框
        message_box = QMessageBox()
        message_box.setText("Please wait until the process is complete.")
        message_box.exec_()
        
def get_filtered_files(directory, prefix, file_suffix):
    """
    Get filtered files from a directory with a specified prefix and suffix.

    Args:
        directory: The path to the directory containing the files.
        prefix: The prefix to filter files.
        file_suffix: The suffix to filter files.
    
    Returns:
        A list of filtered file names.
    """
    if os.path.exists(directory):
        all_files = os.listdir(directory)
        filtered_files = [file for file in all_files if file.startswith(prefix) and file.endswith(file_suffix)]
    else:
        filtered_files = []
    
    return filtered_files


def load_data_frames(filtered_files, directory):
    """
    Load data from the filtered files into a single DataFrame.

    Args:
        filtered_files: A list of filtered file names.
        directory: The path to the directory containing the files.

    Returns:
        A concatenated DataFrame containing data from all filtered files.
    """
    frames = []
    for file in filtered_files:
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path)
        frames.append(df)

    return pd.concat(frames, axis=0, ignore_index=True)


def calculate_mean_accuracy_and_itr(frames, win):
    """
    Calculate mean accuracy and ITR for the given DataFrame and window length.

    Args:
        frames: A DataFrame containing data from all filtered files.
        win: The main window instance.

    Returns:
        A tuple containing the mean accuracy and mean ITR for the given window length.
    """
    filtered_rows = frames[frames['Window Length'] == win.config.winLEN]

    if not filtered_rows.empty:
        mean_accuracy = filtered_rows['Accuracy'].mean()
        mean_itr = filtered_rows['ITR'].mean()
    else:
        mean_accuracy = None
        mean_itr = None
    
    return mean_accuracy, mean_itr


def update_train_accuracies(filtered_rows, win):
    """
    Update the train accuracy values for each key in the main window's key list.

    Args:
        filtered_rows: A DataFrame containing data from all filtered files.
        win: The main window instance.
    """
    individual_accuracies = filtered_rows['Individual Accuracies'].apply(lambda x: np.fromstring(x[1:-1], sep=', '))

    averaged_individual_accuracies = individual_accuracies.mean()

    for i, avg_acc in enumerate(averaged_individual_accuracies):
        win.keyboard_manager.current_key_list.keys[i].trainAcc = avg_acc


def update_test_accuracies(frames, win):
    """
    Update the test accuracy values for each key in the main window's key list.

    Args:
        frames: A DataFrame containing data from all filtered files.
        win: The main window instance.
    """
    accuracy_dict = {}

    for target in range(1, len(win.keyboard_manager.current_key_list.keys) + 1):
        target_rows = frames[frames['event'] == target]
        if not target_rows.empty:
            correct_predictions = target_rows[target_rows['event'] == target_rows['result']]
            accuracy = len(correct_predictions) / len(target_rows)
            accuracy_dict[target] = accuracy

    for i, key in enumerate(win.keyboard_manager.current_key_list.keys):
        target = i + 1
        if target in accuracy_dict:
            key.testAcc = accuracy_dict[target]
        else:
            key.testAcc = None