import sys
sys.path.append('.')
import time
from CommonSystem.Config import Config
from StimulationSystem.stimulationOperator import stimulationOperator
from StimulationSystem.StimulationProcess.StimulationController import StimulationController 
from CommonSystem.MessageReceiver.ExchangeMessageManagement import ExchangeMessageManagement
from StimulationSystem.UICreator.UIFactory import UIFactory
from OperationSystem.operationOperator import operationOperator
from OperationSystem.AnalysisProcess.AnalysisController import AnalysisController
from OperationSystem.Streaming.NeuroScanEEG import NeuroScanEEGThread
import multiprocessing
import pickle
import os

# Define a function to start the stimulation message management process
def stimulation_worker(config, progress_manager):

    # Create an instance of the stimulation operator class
    stimulationOperators = stimulationOperator()
    
    if config.MODE =="PREVIEW":
        
        # Create an instance of the stimulation controller class and initialize it
        stimulator = StimulationController().initial(config, None, progress_manager = progress_manager)
        
    else:
        
        # Create an instance of the message management class and start the service
        stimMessenger = ExchangeMessageManagement('server', stimulationOperators, config)
        stimMessenger.start()

        # Associate the stimulation operator class with the message management class
        stimulationOperators.messenger = stimMessenger

        # Create an instance of the stimulation controller class and initialize it
        stimulator = StimulationController().initial(config, stimMessenger, progress_manager = progress_manager)
        
        progress_manager["text"] = "Waiting for connection..."
        
        # Send the "STON" message to indicate the start of stimulation presentation
        message = 'STON'
        stimMessenger.send_exchange_message(message)
        
        
        # Check if the stimulation presentation has started
        while stimMessenger.state.status != 'TNOK':
            time.sleep(0.1)
        
        
    progress_manager["value"] = 101
    progress_manager["text"] = "Preparation done! Stimulating..."
    
    # Loop through the stimulation presentation until it ends
    while True:
        
        stimulator.run()
        time.sleep(0.1)

        # Do final clean up before ending
        if stimulator.end == True:
            stimulator.run()
            
            if config.MODE !="PREVIEW":
                
                stimMessenger.send_exchange_message('EXIT')
                stimMessenger.stop()
                
            break


# Define a function to start the operation message management process
def operation_worker(config, progress_manager):
    # Start the control reception and result management
    operationOperators = operationOperator()  # Processing side receives message processing function

    # Exchange information center manager
    operationMessenger = ExchangeMessageManagement('client', operationOperators, config)
    # Start data exchange with the stimulation system
    operationMessenger.start()

    # Amplifier settings
    dataStreaming = NeuroScanEEGThread(config=config, keepEvent=True)
    dataStreaming.connect()

    operationOperators.messenger = operationMessenger
    operationOperators.streaming = dataStreaming

    # Analysis detection controller
    controller = AnalysisController().initial(config, dataStreaming, operationMessenger,progress_manager=progress_manager)

    # Start data reception on the acquisition side
    dataStreaming.start()
    
    # Wait for stimulation to start
    print('Put on hold for stimulation, current state: %s' % operationMessenger.state.control_state)

    while operationMessenger.state.control_state != 'STON':
        # Wait for start processing flag
        time.sleep(0.5)
        
    # Analyze
    while operationMessenger.state.control_state != 'EXIT':
        controller.run()
        time.sleep(0.1)

    # Stop the exchange message center and amplifier
    operationMessenger.stop()
    dataStreaming.disconnect()
    
  
def parallel_process(config):
  operation_messenager_process = multiprocessing.Process(target=operation_worker, args=(config,))

  # start the child process
  operation_messenager_process.start() # calculation child process
  stimulation_worker(config) # main process

  operation_messenager_process.join()
  
  
if __name__ == "__main__":
    # Load the config object from the file using pickle
    with open("CommonSystem"+os.sep+"config.pkl", "rb") as f:
        config = pickle.load(f)

    # 配置系统参数
    # config.connect_info(COM='5EFC', streaming_ip='183.173.120.15', streaming_port=4455, host_ip='127.0.0.1')
    
    
    #%%  multi processes
  
    # operation_messenager_process = multiprocessing.Process(target=operation_worker, args=(config,))
    stimulation_messenger_process = multiprocessing.Process(target=stimulation_worker, args=(config,))
    # operation_messenager_process.start()
    stimulation_messenger_process.start()
    
    
    #%% normal process
    operation_worker(config)
    # stimulation_worker(config)
    
    #%% if still alive than close
    
    # if not operation_messenager_process.is_alive() and not stimulation_messenger_process.is_alive():
        
    # if not operation_messenager_process.is_alive():
        
    if not stimulation_messenger_process.is_alive():
        
        # operation_messenager_process.join()
        stimulation_messenger_process.join()
        