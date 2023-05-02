import os
import sys
import math
import pickle
import threading
import matplotlib.pyplot as plt
import matplotlib.patches
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMessageBox

sys.path.append('.')
from StimulationSystem.UICreator.UIFactory import fig2data, frameLoader
from StimulationSystem.UICreator.StimTargetRect import StimTargetRect
from GraphicUserInterface.ui_processing import run_radio_button_clicked
from CommonSystem.Config import config_make_file

###################################################################################### 
#                                                                                    #
#                                                                                    #
#                                Frame Generation                                    #
#                                                                                    #
#                                                                                    #
###################################################################################### 

def frame_maker(win):
    """
    Generate frames for the user interface and save them.
    """
    # check if frames are ready
    if win.keyboard_manager.frames_ready == False:
        
        # Get the frames
        win.process_manager.progress_manager["text"] = "Generating frames..."
        frames = getFrames_for_ui(win.keyboard_manager, win.process_manager, win.user_manager.current_user.name, 
                                  resolution = (map(int, win.screenResolutionsLineEdit.text().split('x'))), refresh_rate = float(win.refreshRateLineEdit.text()))
        win.process_manager.progress_manager["text"] = "Saving frames..."
        saveFrames(win.keyboard_manager, frames, win.process_manager)
        win.keyboard_manager.frames_ready = True
        
    win.process_manager.progress_manager["text"] = "Starting a few operations... please wait..."
    
    win.MULTIPROCESS_RUN_START = True
    

def saveFrames(mgr, frames, prc):    
    """
    Save the generated frames to the specified folder.
    """
    # clear out old frames
    for f in os.listdir(mgr.saveFolder):
        os.remove(os.path.join(mgr.saveFolder, f))
    
    # save frames
    initFrame = frames.initFrame
    plt.imsave(mgr.saveFolder+os.sep+'initial_frame.png', initFrame)

    rectSet = frames.rectSet
    with open(mgr.saveFolder+os.sep+'STI.pkl', "wb+") as fp:
        pickle.dump(rectSet, fp, protocol=pickle.HIGHEST_PROTOCOL)
        
    prc.progress_manager["value"] = 100


def getFrames_for_ui(mgr, prc, personName, resolution=(1920, 1080), refresh_rate = 60):
    """
    Get frames for the user interface with specified resolution and person name.
    """
    # Unpack resolution values
    x_resolution, y_resolution = resolution

    # Initialize necessary variables and lists
    frameSet = []
    rectSet = []
    size = mgr.current_key_list.cubeSize
    rectINX = 0

    # Create StimTargetRect objects and append them to rectSet
    for key in mgr.current_key_list.keys:
        rect = StimTargetRect('ssvep', rectINX, personName, [(key.location_x), (key.location_y)], size,
                              refresh_rate, key.frequency, key.phase, 255)
        rectINX += 1
        rectSet.append(rect)

    # Adjust resolution if half_screen is True
    if mgr.current_key_list.half_screen:
        if mgr.current_key_list.MouseOrKeyboard == "Mouse":
            x_resolution //= 2
        else:
            y_resolution //= 2

    # Set up the figure and axes for drawing
    f = plt.figure(figsize=(x_resolution / 100, y_resolution / 100), facecolor='none', dpi=100)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
    plt.rcParams['axes.unicode_minus'] = False
    current_axis = plt.gca()

    # Initialize progress value
    progress = 1

    # Draw keys on the figure
    for key in mgr.current_key_list.keys:
        brightness = 1
        draw_one_key(mgr, key, brightness, x_resolution, y_resolution, current_axis)

        prc.progress_manager["value"] = progress
        progress += 1

    # Finalize figure and append to frameSet
    plt.axis('off')
    frameSet.append(fig2data(f))
    plt.close(f)

    # Create and initialize a frameLoader object
    frames = frameLoader()
    frames.initFrame = frameSet.pop(0)
    frames.rectSet = rectSet

    return frames



###################################################################################### 
#                                                                                    #
#                                                                                    #
#                               Drawing Functions                                    #
#                                                                                    #
#                                                                                    #
###################################################################################### 
 
def draw_one_key(mgr,key,brightness,x_resolution,y_resolution,current_axis):
    """
    Generate refresh pictures and preview them on the user interface.
    """
    x_loc = key.location_x / x_resolution
    y_loc = key.location_y / y_resolution
    x_size = mgr.current_key_list.cubeSize / x_resolution
    y_size = mgr.current_key_list.cubeSize / y_resolution

    target = matplotlib.patches.Rectangle((x_loc,y_loc),
                        x_size,y_size,
                        linewidth=1, facecolor=[brightness, brightness, brightness])
    # 写上字
    v = plt.text(x_loc + x_size / 2,
            y_loc + y_size / 2, key.key_name,
            fontsize = mgr.current_key_list.fontSize, horizontalalignment='center', verticalalignment='center')
    
    current_axis.add_patch(target)

def make_refresh_pics(win):
    '''
    make refresh pics and preview them on the UI.
    '''
    x_resolution,y_resolution = map(int, win.screenResolutionsLineEdit.text().split('x'))
    
    if win.keyboard_manager.current_key_list.half_screen == True:
        if win.keyboard_manager.current_key_list.MouseOrKeyboard =="Mouse":
            x_resolution = x_resolution//2
        else:
            y_resolution = y_resolution//2
    
    f = plt.figure(figsize=(x_resolution/100, y_resolution/100), facecolor='none', dpi=70)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1, bottom=0, left=0,
                        right=1, hspace=0, wspace=0)

    plt.rcParams['axes.unicode_minus'] = False  # 这两行需要手动设置
    current_axis = plt.gca()
    
    
    win.keyboard_manager.current_key_list.cubeSize = int(win.cubeSizeLineEdit.text())
    win.keyboard_manager.current_key_list.fontSize = int(win.fontSizeLineEdit.text())
    
    # start writing
    for key in win.keyboard_manager.current_key_list.keys:
            
        brightness = 1
        draw_one_key(win.keyboard_manager,key,brightness,x_resolution,y_resolution,current_axis)


    plt.axis('off')
    key_name_frame = fig2data(f)
    plt.close(f)
    keyname_pic_loc = 'GraphicUserInterface'+os.sep+'images'+os.sep+'key_preview.png'
    plt.imsave(keyname_pic_loc, key_name_frame)
            
    f = plt.figure(figsize=(x_resolution/100, y_resolution/100), facecolor='none', dpi=70)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1, bottom=0, left=0,
                        right=1, hspace=0, wspace=0)

    plt.rcParams['axes.unicode_minus'] = False  # 这两行需要手动设置
    current_axis = plt.gca()

    # if win.screenResolutionComboBox.currentText() =="1920x1080":
    #     x_resolution,y_resolution = (1920,1080)

    win.keyboard_manager.current_key_list.cubeSize = int(win.cubeSizeLineEdit.text())
    stim_font_size = round(int(win.keyboard_manager.current_key_list.fontSize)/2+2)
    # if stim_font_size < 1:
    #     stim_font_size = 1

    for key in win.keyboard_manager.current_key_list.keys:
        brightness = 1
                
        x_loc = key.location_x / x_resolution
        y_loc = key.location_y / y_resolution
        x_size = win.keyboard_manager.current_key_list.cubeSize / x_resolution
        y_size = win.keyboard_manager.current_key_list.cubeSize / y_resolution

        
        # if key.run_instruction.lower() != "space":
            # 画一个正方形
        target = matplotlib.patches.Rectangle((x_loc,y_loc),
                            x_size,y_size,
                            linewidth=1, facecolor=[brightness, brightness, brightness])
        # 写上字
        v = plt.text(x_loc + x_size / 2,
                y_loc + y_size / 2, f"{round(key.frequency,2)} Hz /\n {round(key.phase/math.pi,2)} π",
                fontsize=stim_font_size, horizontalalignment='center', verticalalignment='center')
        
        current_axis.add_artist(v)
        current_axis.add_patch(target)

    plt.axis('off')
    key_name_frame = fig2data(f)
    plt.close(f)
    freq_pic_loc = 'GraphicUserInterface'+os.sep+'images'+os.sep+'freq_preview.png'
    plt.imsave(freq_pic_loc, key_name_frame)
    
    # preview images
    win.keyboard_preview_pic.setPixmap(QtGui.QPixmap(keyname_pic_loc))
    win.frequency_preview_pic.setPixmap(QtGui.QPixmap(freq_pic_loc))

###################################################################################### 
#                                                                                    #
#                                                                                    #
#                            Main Execution Functions                                #
#                                                                                    #
#                                                                                    #
###################################################################################### 

def first_level_run(win):
    """
    Main function to run first before calling psychopy and handle errors.
    """
    # If the process is not running, start it
    if win.process_manager.run_blocking == False:
        win.process_manager.run_blocking = True

        # Renew the current user
        win.user_manager.current_user.renew(win)

        # If the current user name is empty, display an error dialog and abort the function
        if win.user_manager.current_user.name == "":
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Error")
            error_dialog.setText("User name cannot be empty!")
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
            win.process_manager.run_blocking = False
            return

        # Show the progress bar and label
        win.progressBar_label.setVisible(True)
        win.progressBar.setVisible(True)

        # Initialize the progress bar
        win.keyboard_manager.stim_length = float(win.stimulusLengthLineEdit.text())
        refresh_rate = float(win.refreshRateLineEdit.text())
        win.keyboard_manager.maxFrames = int(win.keyboard_manager.stim_length * refresh_rate)

        # Construct the config file
        config_make_file(win)

        # Start the main process in a separate thread
        thread = threading.Thread(target=frame_maker, args=(win,), name='frames generating thread')
        thread.start()

    # If the process is already running, display a message box
    else:
        message_box = QMessageBox()
        message_box.setText("Please wait until the process is complete.")
        message_box.exec_()


def preview_flickering(win):
    """
    To run in PREVIEW mode.
    """
    win.renew_all()
    win.process_manager.run_mode = "PREVIEW"
    first_level_run(win)
        

def processing_run(win):
    """
    Execute the main processing on the user interface.
    """
    win.renew_all()
    first_level_run(win)


###################################################################################### 
#                                                                                    #
#                                                                                    #
#                               Completion Function                                  #
#                                                                                    #
#                                                                                    #
###################################################################################### 

def flickering_on_complete(win):
    """
    Actions to perform once the flickering effect is complete.
    """
    win.process_manager.progress_manager["text"] = "Run Complete."
    print(win.process_manager.progress_manager["text"])

    win.process_manager.run_blocking = False
    run_radio_button_clicked(win)

    win.process_manager.progress_manager["value"] = 101