import time
import sys

# Append the current directory to the system path
sys.path.append('.')

from StimulationSystem.StimulationProcess.StimulationController import StimulationController 
import pickle
import os

if __name__ == "__main__":
  
    # Load the config object from the file using pickle
    with open("CommonSystem"+os.sep+"config.pkl", "rb") as f:
        config = pickle.load(f)


    # load the pictures
    stimulator = StimulationController().initial(config, None)

    while stimulator.end != True:
        stimulator.run()
        time.sleep(0.01)
        
    stimulator.run()
