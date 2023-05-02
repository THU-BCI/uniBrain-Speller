import pyautogui
import time
from PyQt5.QtWidgets import QMessageBox

def customizedFunction(instruction):
    '''
    Do something with the instruction, instruction is the key's label text.
    
    Example:
    if instruction == "↖︎":
        x_offset, y_offset = -100, -100
    pyautogui.moveRel(x_offset, y_offset, duration=1)

    '''
    if instruction =="help":
        pyautogui.moveRel(200, 200, duration=0.5)
    
    pass

def customizedTestFunction(instruction):
    time.sleep(0.5)
    
    try:
        customizedFunction(instruction)
        
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("An error occurred while running the function.")
        error_dialog.setInformativeText(f"Error message: {str(e)}\nPlease edit and debug the function.")
        error_dialog.exec_()