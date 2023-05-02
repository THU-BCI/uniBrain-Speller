import importlib
import os
import customized_function
import platform
import subprocess
import csv
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QBrush, QDoubleValidator, QPixmap
from ui_StimulusControl import preview_flickering, make_refresh_pics
from ui_processing import load_prc_table_with_key
import keyboard_function
import pathlib
import pickle
import threading

class KeyboardManager:
    def __init__(self):
        """Manages keyboard settings, UI interactions, and key lists."""
        self.key_lists = []
        self.current_key_list = None
        self.frames_ready = False
        self.stim_length = 1
        self.maxFrames = int(60 * self.stim_length)
        self.saveFolder = os.path.join(os.getcwd(), 'StimulationSystem', 'pics', 'ssvep')
        if not os.path.exists(self.saveFolder):
            os.makedirs(self.saveFolder)
        self.blockNUM = 1
        self.spareFrameSet = None
        self.spareInitSet = None
        self.cueTime = 1
        self.halfScreen = False
        self.halfScreenPos = 0
        
        
    def add_key_list(self, name, key_list):
        """Adds a key list to the manager."""
        new_keys = []
        for key in key_list.keys:
            new_keys.append(Key(key.key_name, key.frequency, key.phase, key.location_x, key.location_y, key.is_default))
        new_key_list = KeyList(name, new_keys, key_list.MouseOrKeyboard)
        new_key_list.two_phase_on = key_list.two_phase_on
        new_key_list.fontSize = key_list.fontSize
        new_key_list.cubeSize = key_list.cubeSize
        new_key_list.stride = key_list.stride
        new_key_list.strideStep = key_list.strideStep
        new_key_list.stim_time = key_list.stim_time
        new_key_list.two_phase = key_list.two_phase
        self.key_lists.append(new_key_list)
    
    def set_current_key_list(self, key_list_name):
        for key_list in self.key_lists:
            if key_list.name == key_list_name:
                self.current_key_list = key_list
                return True
        return False
    def refresh_UI(self,win,row):
        win.mouseStrideLengthLineEdit.setText(str(self.current_key_list.stride))
        win.strideStepLineEdit.setText(str(self.current_key_list.strideStep))
        win.stimulusLengthLineEdit.setText(str(win.keyboard_manager.current_key_list.stim_time))
        
        
        if win.keyboard_manager.current_key_list.two_phase == True:
            # mouse with two phases
            if (win.keyboard_manager.current_key_list.keys[row].run_instruction == "Drag" 
                or win.keyboard_manager.current_key_list.keys[row].run_instruction == "⇧"):
                
                # win.keyboard_manager.current_key_list.two_phase_on = not win.keyboard_manager.current_key_list.two_phase_on
                toggle_font_color(win.keyboard_table.item(row, 0))
                
    def load_data(self,mgr,win):
        self.key_lists = mgr.key_lists
        
        get_key = self.set_current_key_list(mgr.current_key_list.name)
        if get_key == False:
            self.current_key_list = self.key_lists[0]
        
        win.keyTypeComboBox.clear()
        for key_list in self.key_lists:
            win.keyTypeComboBox.addItem(key_list.name)
        keyboard_selection_changed(win)
        
        
        self.frames_ready = False
        self.stim_length = mgr.stim_length
        self.maxFrames = int(60 * self.stim_length)
        self.saveFolder = os.path.join(os.getcwd(), 'StimulationSystem', 'pics', 'ssvep') # for saving the pictures
        if os.path.exists(self.saveFolder) is False:
            os.makedirs(self.saveFolder)
            
        # for stimulus
        self.blockNUM = mgr.blockNUM
        self.spareFrameSet = mgr.spareFrameSet
        self.spareInitSet = mgr.spareInitSet
        self.cueTime = mgr.cueTime
        self.halfScreen = mgr.halfScreen
        self.halfScreenPos = mgr.halfScreenPos
        self.reverse_renew(win)
        
        
        
            
    def renew(self,win):
        """Updates settings based on user input."""
        if (self.stim_length != float(win.stimulusLengthLineEdit.text()) or 
            self.maxFrames != int(60 * self.stim_length)):
            self.frames_ready = False
    
        self.stim_length = float(win.stimulusLengthLineEdit.text())
        self.maxFrames = int(60 * self.stim_length)
        self.cueTime = float(win.cueTimeLineEdit.text())
        
        
        self.current_key_list.stride = int(win.mouseStrideLengthLineEdit.text())
        self.current_key_list.strideStep = int(win.strideStepLineEdit.text())
        
        
        # Show or hide the formFrame based on the checked radio button
        if win.fullScreenRadioButton.isChecked():
            self.halfScreen = False
            win.stimPositionFormFrame.hide()
        elif win.halfScreenRadioButton.isChecked():
            self.halfScreen = True
            win.stimPositionFormFrame.show()
        
    def reverse_renew(self,win):
        """Updates UI based on current settings."""
        win.stimulusLengthLineEdit.setText(str(self.stim_length))
        win.cueTimeLineEdit.setText(str(self.cueTime))
        win.mouseStrideLengthLineEdit.setText(str(self.current_key_list.stride))
        win.strideStepLineEdit.setText(str(self.current_key_list.strideStep))
        
        if win.keyboard_manager.halfScreen:
            win.halfScreenRadioButton.setChecked(True)
            win.stimPositionFormFrame.show()
        else:
            win.fullScreenRadioButton.setChecked(True)
            win.stimPositionFormFrame.hide()
        
        if win.keyboard_manager.halfScreenPos == 0:
            win.stimScreen0Position.setChecked(True)
        else:
            win.stimScreen1Position.setChecked(True)
            

class KeyList:
    
    def __init__(self, name, keys, MouseOrKeyboard = "Mouse"):
        """Represents a list of keys and related settings."""
        self.name = name
        self.keys = keys
        
        if "Mouse 13 keys" in self.name or "Keyboard 43 keys" in self.name:
            self.two_phase = True
        else:
            self.two_phase = False
            
            
        self.MouseOrKeyboard = MouseOrKeyboard
        
        if "HS" in self.name:
            self.half_screen = True
        else:
            self.half_screen = False
        
        if self.MouseOrKeyboard == "Mouse":
            if self.half_screen == False:
                self.fontSize = 40
                self.cubeSize = 180
            else:
                self.fontSize = 30
                self.cubeSize = 130
                
            self.stride = 200
            self.strideStep = 50
        else:
            if self.half_screen == False:
                self.fontSize = 22
                self.cubeSize = 100
            else:
                self.fontSize = 17
                self.cubeSize = 70
        
            self.stride = 0
            self.strideStep = 0
        self.stim_time = 1
        self.two_phase_on = False
        self.current_thread = None
        
    def join_current_thread(self):
        """Waits for the current thread to finish operate."""
        if self.current_thread is not None and self.current_thread.is_alive():
            self.current_thread.join()
        
    def save(self,file):
        """Saves the key list to a file."""
        pickle.dump(self, file)
    
    def load(self,win,fname):
        """Loads a key list from a file."""
        with open(fname,'rb') as file:
            self = pickle.load(file)
        # self.reverseRenew(win)
    
    
class Key:
    def __init__(self, key_name, frequency, phase, location_x, location_y, is_default = False):
        """Represents an individual key and related properties."""
        self.key_name = key_name
        self.frequency = frequency
        self.phase = phase
        self.location_x = location_x
        self.location_y = location_y
        self.run_instruction = self.key_name
        self.is_default = is_default
        self.trainAcc = None
        self.testAcc = None
        self.output = 0 # output count
        
    def run_key_function(self, key_list, fake_run = False, wait = False):
        """
        Args:
            key_list (_type_): the key_list that the key belongs to.
            fake_run (bool, optional): fake_run true means running for preview, fake_run false means true output that will aggregate to its output attribute.
                                        It defaults to False.
        """
        
        # Ensure the previous thread is completed before starting a new one
        if wait == False:
            key_list.join_current_thread()
        
        if self.is_default:
            if key_list.MouseOrKeyboard == "Mouse":
                # keyboard_function.mouse_key_function(self.run_instruction, key_list)
                
                if wait == False:
                    # Run mouse_key_function in a new thread
                    t = threading.Thread(target=keyboard_function.mouse_key_function, args=(self.run_instruction, key_list, fake_run))
                    t.start()
                else:
                    keyboard_function.mouse_key_function(self.run_instruction, key_list, fake_run)
                
            else:
                # keyboard_function.keyboard_key_function(self.run_instruction)
                
                if wait == False:
                    # Run keyboard_key_function in a new thread
                    t = threading.Thread(target=keyboard_function.keyboard_key_function, args=(self.run_instruction, key_list, fake_run))
                    t.start()
                else:
                    
                    keyboard_function.keyboard_key_function(self.run_instruction, key_list, fake_run)
                
            
        else:
            # Reload the module to ensure that any changes made to it are reflected in the program
            importlib.reload(customized_function)
            
            if wait == False:
                # Run keyboard_key_function in a new thread
                t = threading.Thread(target=customized_function.customizedTestFunction, args=(self.key_name,))
                t.start()
            else:
                customized_function.customizedTestFunction(self.key_name)
        
        if fake_run == False:
            self.output +=1
            
        if wait == False:
            # Store the new thread in key_list
            key_list.current_thread = t


def UI_init(win):
    """
    Initializes the user interface for the keyboard configuration window.
    """
    reset(win)    
    
    # connect the buttons to the functions
    win.keyTypeComboBox.currentIndexChanged.connect(lambda: keyboard_selection_changed(win))
    win.refresh_key_button.clicked.connect(lambda: make_refresh_pics(win))
    win.keyboard_default_button.clicked.connect(lambda: keyboard_back_to_default(win))
    win.del_button.clicked.connect(lambda: del_button_clicked(win))
    win.add_button.clicked.connect(lambda: add_button_clicked(win))
    win.saveKeyboard_button.clicked.connect(lambda: save_keyboard(win))
    win.loadKeyboard_button.clicked.connect(lambda: load_keyboard(win))
    win.preview_key_button.clicked.connect(lambda: preview_flickering(win))
    win.preview_keyboard_frame.setStyleSheet("background-color: black;")
    double_validator = QDoubleValidator(0.3, 10, 1)
    win.stimulusLengthLineEdit.setValidator(double_validator)
    win.cueTimeLineEdit.setValidator(double_validator)
    
    
    # Connect the radio buttons to the 'toggle_frame' method
    win.fullScreenRadioButton.toggled.connect(lambda: toggle_frame(win))
    win.halfScreenRadioButton.toggled.connect(lambda: toggle_frame(win))
    win.stimScreen0Position.toggled.connect(lambda: toggle_screen_pos(win))
    win.stimScreen1Position.toggled.connect(lambda: toggle_screen_pos(win))


def reset(win):
    """
    Resets the keyboard configuration window to its default state.
    """
    win.keyboard_manager = KeyboardManager()
    win.keyTypeComboBox.clear()
    
    # Load all the default keyboards into ComboBox
    path = "GraphicUserInterface" + os.sep + "keyboard_list" + os.sep
    csv_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".csv")]
    csv_files.reverse()  # Reverse the list of CSV files
    for file_name in csv_files:
        key_list = read_csv_file(path + file_name)
        win.keyTypeComboBox.addItem(key_list.name)
        win.keyboard_manager.add_key_list(key_list.name, key_list)

    # Set active selection to "Mouse 13 keys"
    key_list_name = "Mouse 13 keys"
    win.keyTypeComboBox.setCurrentText(key_list_name)
    win.keyboard_manager.set_current_key_list(key_list_name)
    win.keyboard_manager.renew(win)
    win.keyboard_manager.reverse_renew(win)
    keyboard_selection_changed(win)
    
def keyboard_selection_changed(win):
    """
    Handles changes in the selected keyboard type in the keyboard configuration window.
    """
    # frames have to generate again
    win.keyboard_manager.frames_ready = False
    
    # To prevent the function from being called when changing the table
    QtCore.QObject.disconnect(win.keyboard_table)
    
    # Get the currently selected keyboard name
    selected_keyboard_name = win.keyTypeComboBox.currentText()
    
    # Set the current key list to the selected keyboard
    win.keyboard_manager.set_current_key_list(selected_keyboard_name)
    
    if "HS" in selected_keyboard_name:
        win.halfScreenRadioButton.setChecked(True)
    else:
        win.fullScreenRadioButton.setChecked(True)
    
    # Refresh the stimulus screen position picture
    if win.keyboard_manager.current_key_list.MouseOrKeyboard == "Mouse":
        # Set the images for stimScreen0Pic and stimScreen1Pic
        pixmap0 = QPixmap(os.path.join("GraphicUserInterface","images","left.png"))
        win.stimScreen0Pic.setPixmap(pixmap0)
        pixmap1 = QPixmap(os.path.join("GraphicUserInterface","images","right.png"))
        win.stimScreen1Pic.setPixmap(pixmap1)
    else:
        # Set the images for stimScreen0Pic and stimScreen1Pic
        pixmap0 = QPixmap(os.path.join("GraphicUserInterface","images","bottom.png"))
        win.stimScreen0Pic.setPixmap(pixmap0)
        pixmap1 = QPixmap(os.path.join("GraphicUserInterface","images","top.png"))
        win.stimScreen1Pic.setPixmap(pixmap1)

    # Load the table!
    load_table_with_key(win, win.keyboard_manager.current_key_list)
    load_prc_table_with_key(win, win.keyboard_manager.current_key_list)
    
    # Refresh the keyboard images
    make_refresh_pics(win)
    
    if hasattr(win, 'process_manager'):
        win.process_manager.refresh_calculation(win, refresh_config=True, message_box=False)
    
    
    # Get the current width limit of the main window
    current_width = win.width() - 90
    
    # adjust the pictures of the both image to ratio
    adjust_picture_size(win,current_width)
    

def load_table_with_key(win, KeyList):
    """
    Loads the key list table with the provided KeyList object.

    Args:
        KeyList (KeyList): The key list object containing the keys.
    """
    win.keyboard_table.clearContents()
    win.keyboard_table.setColumnCount(7)
    
    # set row height to 40
    win.keyboard_table.verticalHeader().setDefaultSectionSize(40)
    
    win.keyboard_table.setHorizontalHeaderLabels( ["Key\nName", "Freq\n(Hz)", "Phase\n(rad)", "Loc\nX", "Loc\nY", "Function", "Del?"])
    win.keyboard_table.setRowCount(len(KeyList.keys))
    win.keyboard_table.horizontalHeader().setStyleSheet("QHeaderView::section { border: 2px solid black; }")

    for i, key in enumerate(KeyList.keys): 
        # Create widgets for each cell
        key_name = QtWidgets.QTableWidgetItem(key.key_name)
        frequency = QtWidgets.QTableWidgetItem(str(key.frequency))
        phase = QtWidgets.QTableWidgetItem(str(key.phase))
        location_x = QtWidgets.QTableWidgetItem(str(int(round(key.location_x))))
        location_y = QtWidgets.QTableWidgetItem(str(int(round(key.location_y))))
        checkbox = QtWidgets.QCheckBox()
        if key.run_instruction == "Drag" or key.run_instruction == "+" or key.run_instruction == "-" or key.run_instruction == "⇧":
            checkbox.setEnabled(False)

        # Set widget properties
        for item in (key_name, frequency, phase, location_x, location_y):
            item.setTextAlignment(QtCore.Qt.AlignCenter)
        
        
        # Create container widget for button
        widget_container_B = QtWidgets.QWidget()
        layoutB = QtWidgets.QHBoxLayout(widget_container_B)
        test_button = QtWidgets.QPushButton("Test")
        edit_button = QtWidgets.QPushButton("Edit")
        layoutB.addWidget(test_button)
        layoutB.setAlignment(QtCore.Qt.AlignCenter)
        test_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        
        # Create container widget for checkbox
        widget_container_C = QtWidgets.QWidget()
        layoutC = QtWidgets.QHBoxLayout(widget_container_C)
        layoutC.addWidget(checkbox)
        layoutC.setAlignment(QtCore.Qt.AlignCenter)

        # Connect signals and slots
        test_button.clicked.connect(lambda checked, row=i: on_test_button_clicked(win,row))
        
        win.keyboard_table.setCellWidget(i, 5, widget_container_B)
        win.keyboard_table.setCellWidget(i, 6, widget_container_C)
        win.keyboard_table.setItem(i, 0, key_name)
        win.keyboard_table.setItem(i, 1, frequency)
        win.keyboard_table.setItem(i, 2, phase)
        win.keyboard_table.setItem(i, 3, location_x)
        win.keyboard_table.setItem(i, 4, location_y)
    
    # refresh the line edits
    win.fontSizeLineEdit.setText(str(KeyList.fontSize))
    win.mouseStrideLengthLineEdit.setText(str(KeyList.stride))
    win.strideStepLineEdit.setText(str(KeyList.strideStep))
    win.cubeSizeLineEdit.setText(str(KeyList.cubeSize))
    
    # Connect signal and slot
    win.keyboard_table.cellChanged.connect(lambda row, column: update_key_list(win, row, column, KeyList))
    
    
def update_key_list(win, row, column, KeyList):
    """
    Updates the key properties in the specified row and column of the key list table.

    Args:
        row (int): The row number of the key in the table.
        column (int): The column number of the key property in the table.
        KeyList (KeyList): The key list object containing the keys.
    """
    win.keyboard_manager.frames_ready = False
    
    key = KeyList.keys[row]
    value = win.keyboard_table.item(row, column).text()
    if column == 0:
        key.key_name = value
    elif column == 1:
        key.frequency = float(value)
    elif column == 2:
        key.phase = float(value)
    elif column == 3:
        key.location_x = int(round(float(value)))
    elif column == 4:
        key.location_y = int(round(float(value)))


def on_edit_button_clicked(win, row):
    """
    Opens the custom function file associated with the key in the specified row in a text editor.

    Args:
        row (int): The row number of the key in the table.
    """
    path = os.path.join("GraphicUserInterface", "customized_function.py")
    
    # Determine the appropriate command to use based on the operating system
    if platform.system() == "Windows":
        vs_command = "code.cmd"
        default_editor = "notepad.exe"
    elif platform.system() == "Darwin":
        vs_command = "code"
        default_editor = "open -e"
    else:
        print("Unsupported operating system.")
        return
    
    # Try opening the file in Visual Studio Code
    try:
        subprocess.Popen([vs_command, path])
    except FileNotFoundError:
        print("Visual Studio Code not found, opening with default text editor.")
        # Open the file with the default text editor if Visual Studio Code is not found
        try:
            subprocess.Popen([default_editor, path])
        except Exception as e:
            print("Error opening file:", e)
            

def on_test_button_clicked(win, row):
    """
    Tests the key function associated with the key in the specified row.

    Args:
        row (int): The row number of the key in the table.
    """
    win.keyboard_manager.current_key_list.stride = int(win.mouseStrideLengthLineEdit.text())
    win.keyboard_manager.current_key_list.strideStep = int(win.strideStepLineEdit.text())
    win.keyboard_manager.current_key_list.stim_time = float(win.stimulusLengthLineEdit.text())
    win.keyboard_manager.current_key_list.keys[row].run_key_function(win.keyboard_manager.current_key_list,fake_run = True)
    win.keyboard_manager.refresh_UI(win,row)
    


def add_button_clicked(win):
    """
    Adds a new key to the key list table.
    """
    # create a new key and add it to current_keys
    new_key = Key("New Key", 0, 0, 0, 0)
    win.keyboard_manager.current_key_list.keys.append(new_key)

    # get the current row count
    row_count = win.keyboard_table.rowCount()
    # insert a new row
    win.keyboard_table.insertRow(row_count)

    # create the widgets for the new row
    key_name = QtWidgets.QTableWidgetItem(" ")
    frequency = QtWidgets.QTableWidgetItem("0")
    phase = QtWidgets.QTableWidgetItem("0")
    location_x = QtWidgets.QTableWidgetItem("0")
    location_y = QtWidgets.QTableWidgetItem("0")

    # Create container widget for button
    widget_container_B = QtWidgets.QWidget()
    layoutB = QtWidgets.QHBoxLayout(widget_container_B)
    test_button = QtWidgets.QPushButton("Test")
    edit_button = QtWidgets.QPushButton("Edit")
    layoutB.addWidget(edit_button)
    layoutB.addWidget(test_button)
    # test_button.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
    layoutB.setAlignment(QtCore.Qt.AlignCenter)
    
    # Create container widget for checkbox
    widget_container_C = QtWidgets.QWidget()
    layoutC = QtWidgets.QHBoxLayout(widget_container_C)
    checkbox = QtWidgets.QCheckBox()
    layoutC.addWidget(checkbox)
    layoutC.setAlignment(QtCore.Qt.AlignCenter)
    
    edit_button.clicked.connect(lambda: on_edit_button_clicked(win,row_count))
    test_button.clicked.connect(lambda: on_test_button_clicked(win,row_count))

    # set the text alignment
    for item in (key_name, frequency, phase, location_x, location_y):
        item.setTextAlignment(QtCore.Qt.AlignCenter)

    # Set the table widget items
    win.keyboard_table.setCellWidget(row_count, 5, widget_container_B)
    win.keyboard_table.setCellWidget(row_count, 6, widget_container_C)
    win.keyboard_table.setItem(row_count, 0, key_name)
    win.keyboard_table.setItem(row_count, 1, frequency)
    win.keyboard_table.setItem(row_count, 2, phase)
    win.keyboard_table.setItem(row_count, 3, location_x)
    win.keyboard_table.setItem(row_count, 4, location_y)


def del_button_clicked(win):
    """
    Deletes the selected keys from the key list table.
    """
    rows_to_delete = []

    # Iterate over the rows in the table
    for row in range(win.keyboard_table.rowCount()):
        # Get the checkbox in the current row
        checkbox_widget = win.keyboard_table.cellWidget(row, 6)
        checkbox = checkbox_widget.findChild(QtWidgets.QCheckBox)

        # If the checkbox is checked, mark the row for deletion
        if checkbox.isChecked():
            rows_to_delete.append(row)

    # Delete the marked rows in reverse order
    for row in reversed(rows_to_delete):
        win.keyboard_table.removeRow(row)
        win.keyboard_manager.current_key_list.keys.pop(row)


def keyboard_back_to_default(win):
    """
    Resets the keyboard configuration window to the default keyboard type.
    """
    QtCore.QObject.disconnect(win.keyTypeComboBox)
    reset(win)
    win.keyTypeComboBox.currentIndexChanged.connect(lambda: keyboard_selection_changed(win))
    win.process_manager.progress_manager["text"] = "Back to Default!"


def save_keyboard(win):
    """
    Saves the current keyboard configuration to a file.
    """
    win.keyboard_manager.current_key_list.cubeSize = int(win.cubeSizeLineEdit.text())
    win.keyboard_manager.current_key_list.fontSize = int(win.fontSizeLineEdit.text())
    win.keyboard_manager.current_key_list.stride = int(win.mouseStrideLengthLineEdit.text())
    win.keyboard_manager.current_key_list.strideStep = int(win.strideStepLineEdit.text())
    win.keyboard_manager.current_key_list.stim_time = float(win.stimulusLengthLineEdit.text())
    
    file_path, _  = QtWidgets.QFileDialog.getSaveFileName(win, 'Save Keyboard', 
                                                    str(pathlib.Path().absolute()) + os.sep,"SSVEP keyboard files (*.keyboard)")
    if file_path:
        # Add to additionalKeyList if not already present
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if file_name not in [kl.name for kl in win.keyboard_manager.key_lists]:
            # Serialize the current_key_list object
            current_key_list = win.keyboard_manager.current_key_list
            serialized_key_list = pickle.dumps(current_key_list)
            
            # Save the serialized object to file
            with open(file_path, 'wb') as f:
                f.write(serialized_key_list)
            
            # Add the key list to the keyboard manager and the combo box
            win.keyboard_manager.add_key_list(file_name, win.keyboard_manager.current_key_list)
            win.keyTypeComboBox.addItem(file_name)

        # Set active selection to the new one
        win.keyboard_manager.set_current_key_list(file_name)
        win.keyTypeComboBox.setCurrentText(file_name)

    make_refresh_pics(win)
    

def load_keyboard(win):
    """
    Loads a keyboard configuration from a file.
    """
    win.keyboard_manager.current_key_list.cubeSize = int(win.cubeSizeLineEdit.text())
    win.keyboard_manager.current_key_list.fontSize = int(win.fontSizeLineEdit.text())
    win.keyboard_manager.current_key_list.stride = int(win.mouseStrideLengthLineEdit.text())
    win.keyboard_manager.current_key_list.strideStep = int(win.strideStepLineEdit.text())
    win.keyboard_manager.current_key_list.stim_time = float(win.stimulusLengthLineEdit.text())
    
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(win, 'Open Keyboard',
                                                    str(pathlib.Path().absolute()) + os.sep,"SSVEP keyboard files (*.keyboard)")
    if file_path:
        # Deserialize the object from the file
        with open(file_path, 'rb') as f:
            serialized_key_list = f.read()
        current_key_list = pickle.loads(serialized_key_list)
        
        # Add the key list to the keyboard manager and the combo box
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if file_name not in [kl.name for kl in win.keyboard_manager.key_lists]:
            win.keyboard_manager.add_key_list(file_name, current_key_list)
            win.keyTypeComboBox.addItem(file_name)

        # Set active selection to the new one
        win.keyboard_manager.set_current_key_list(file_name)
        win.keyTypeComboBox.setCurrentText(file_name)
        
    make_refresh_pics(win)
    

def read_csv_file(file_path):
    """
    Reads a CSV file containing key information and creates a KeyList object.

    Args:
        file_path (str): The path to the CSV file.
    """
    keys = []
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # skip the header row
        for row in reader:
            key = Key(row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4]), is_default = True)
            keys.append(key)

    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # if filename consists of "mouse" in any case:
    if "mouse" in filename.lower():
        key_list = KeyList(filename, keys, "Mouse")
    else:
        key_list = KeyList(filename, keys, "Keyboard")
        
    return key_list


def adjust_picture_size(win,max_width):
    """
    Adjusts the width of the preview images according to the aspect ratio of the selected keyboard type.

    Args:
        max_width (int): The maximum width of the preview images.
    """
    if "HS" in win.keyboard_manager.current_key_list.name:
        
        if win.keyboard_manager.current_key_list.MouseOrKeyboard == "Mouse":
            adjust_width_to_ratio(win.keyboard_preview_pic, max_width, 8/9)
            adjust_width_to_ratio(win.frequency_preview_pic, max_width, 8/9)
        else:
            adjust_width_to_ratio(win.keyboard_preview_pic, max_width, 16/4.5)
            adjust_width_to_ratio(win.frequency_preview_pic, max_width, 16/4.5)
    else:
        adjust_width_to_ratio(win.keyboard_preview_pic, max_width, 16/9)
        adjust_width_to_ratio(win.frequency_preview_pic, max_width, 16/9)


def adjust_width_to_ratio(input,max_width, ratio):
    """
    Adjusts the width of a UI element according to a given ratio.

    Args:
        input (UI element): The UI element to be adjusted.
        max_width (int): The maximum width of the UI element.
        ratio (float): The desired aspect ratio of the UI element.
    """
    pixmap = input.pixmap()

    if pixmap is not None:
        
        new_width = int(max_width*0.37)
        new_height = int(new_width / ratio)
        input.setMaximumSize(QtCore.QSize(new_width, new_height))
        
def toggle_font_color(item):    
    """
    Toggles the font color of a QTableWidgetItem object between black and white.

    Args:
        item (QTableWidgetItem): The QTableWidgetItem object to toggle the font color.
    """
    # Check the current font color of the item
    current_color = item.foreground().color()

    # If the current color is red, change it to the default color (black)
    if current_color == QColor(0, 0, 255):
        item.setForeground(QBrush(QColor(0, 0, 0)))
    # If the current color is not red, change it to red
    else:
        item.setForeground(QBrush(QColor(0, 0, 255)))
        

def toggle_frame(win):
    """
    Handles the event if half frame or full frame is selected.
    """
    # Show or hide the formFrame based on the checked radio button
    if win.fullScreenRadioButton.isChecked():
        win.keyboard_manager.halfScreen = False
        win.stimPositionFormFrame.hide()
    elif win.halfScreenRadioButton.isChecked():
        win.keyboard_manager.halfScreen = True
        win.stimPositionFormFrame.show()
        
        
def toggle_screen_pos(win):
    """
    Handles the event of the position of the half frame to be put.
    """
    # Show or hide the formFrame based on the checked radio button
    if win.stimScreen0Position.isChecked():
        win.keyboard_manager.halfScreenPos = 0
    elif win.stimScreen1Position.isChecked():
        win.keyboard_manager.halfScreenPos = 1
    
    

    




        


