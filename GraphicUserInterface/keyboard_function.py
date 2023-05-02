import math
import pyautogui
pyautogui.FAILSAFE = False
import time
from PyQt5.QtWidgets import QMessageBox

def mouse_key_function(instruction, key_list, fake_run = False):
    
    stride = key_list.stride
    stim_time = key_list.stim_time
    
    diagonal = math.sqrt(pow(stride, 2)/ 2)
    if instruction == "↖︎":
        x_offset = -diagonal
        y_offset = -diagonal
    elif instruction == "↑":
        x_offset = 0
        y_offset = -stride
    elif instruction == "↗︎":
        x_offset = diagonal
        y_offset = -diagonal
    elif instruction == "←":
        x_offset = -stride
        y_offset = 0
    elif instruction == "→":
        x_offset = stride
        y_offset = 0
    elif instruction == "↙︎":
        x_offset = -diagonal
        y_offset = diagonal
    elif instruction == "↓":
        x_offset = 0
        y_offset = stride
    elif instruction == "↘︎":
        x_offset = diagonal
        y_offset = diagonal
    elif instruction == "Drag":
        # stimulate a mode change between True and False
        if key_list.two_phase_on == True:
            key_list.two_phase_on = False
        else:
            key_list.two_phase_on = True
        return
    elif instruction == "+":
        # stimulate a stride length increase
        key_list.stride += key_list.strideStep
        if key_list.stride > 450:
            key_list.stride = 450
        return
    elif instruction == "-":
        # stimulate a stride length decrease
        key_list.stride -= key_list.strideStep
        if key_list.stride < 1:
            key_list.stride = 1
        return
    elif instruction == "L":
        # simulate a left-click
        if fake_run:
            time.sleep(0.25*stim_time)
        pyautogui.click()
        return
    elif instruction == "R":
        # simulate a right-click
        if fake_run:
            time.sleep(0.25*stim_time)
        pyautogui.rightClick()
        return
    else:
        # Display an error message in a message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Invalid instruction")
        msg.setWindowTitle("Error")
        msg.exec_()
        return
    
    if fake_run:
        time.sleep(0.25 * stim_time)
    if key_list.two_phase_on == False:
        pyautogui.moveRel(x_offset, y_offset, duration=0.5*stim_time)
    else:
        pyautogui.dragRel(x_offset, y_offset, duration=0.5*stim_time)
    return

                
def keyboard_key_function(instruction, key_list, fake_run = False):
    stim_time = key_list.stim_time
    if fake_run:
        time.sleep(0.25 * stim_time)

    shift_mapping = {
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")",
        ",": "<",
        ".": ">",
        "/": "?",
    }

    special_keys = {
        "←": "backspace",
        " ": "space",
        "⇧": "shift",
        "↵": "enter",
    }

    if instruction in special_keys:
        key = special_keys[instruction]
        if key == "shift":
            key_list.two_phase_on = True
            return
        pyautogui.press(key)
    elif instruction in shift_mapping or instruction.isupper():
        if key_list.two_phase_on:
            if instruction in shift_mapping:
                key = shift_mapping[instruction]
            else:
                key = instruction
        else:
            if instruction.isupper():
                key = instruction.lower()
            else:
                key = instruction
        pyautogui.press(key)
    else:
        # Display an error message in a message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Invalid instruction")
        msg.setWindowTitle("Error")
        msg.exec_()
        return

    if key_list.two_phase_on:
        key_list.two_phase_on = False

    return