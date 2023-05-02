import numpy as np
import math
import string

class stiConfig():
    def __init__(self, paradigm):
        
        self.paradigm = paradigm        #wn, wn_shift, ssvep, wn_784targets, wn_highfreq
        self.saveAdd = 'picFolder'
        self.refreshRate = 60
        self.stiLEN = 3
        self.resolution=(1920,1080)
        self.layout = (5,8)       #
        self.cubicSize = 140         #27
        self.interval = 50           #5
        self.initWidth, self.initHeight = (225, 90)         #225,90

        self.frequency = np.linspace(8.0, 15.8, 40)
        self.phase = np.tile(np.arange(0, 2, 0.5)*math.pi, 10)
        char = list(string.ascii_uppercase) + \
            list(np.arange(10))+['.', ' ', ',', 'Del']
        
        ordered_char = []
        for i in range(8):
            for j in range(5):
                ordered_char.append(char[j*8+i])

        # ordered_char.append('')

        self.displayChar = ordered_char
        # self.trialNUM_eachblock = trialNUM_eachblock

        pass

