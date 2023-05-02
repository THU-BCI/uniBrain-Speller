import numpy as np
import math
import scipy.io as scio


class StimTargetRect():
    def __init__(self, paradigm, rectINX, personName, site_point, rect_size, fs, frequency, start_phase, max_amplitude):
        
        self.personName = personName
        self.paradigm = paradigm
        self.rectINX = rectINX
        self.site_point = site_point
        self.rect_size = rect_size
        self.fs = fs
        self.frequency = frequency
        self.start_phase = start_phase
        self.max_amplitude = max_amplitude
        self.form_flag_matrix = np.ones(rect_size, dtype = 'bool')
        self.position = self.covert2psycho()
        
    def cal_brightness(self, frame_no, paradigm):
        
        if paradigm=='wn':
            stim = scio.loadmat('code\\finalstim.mat')['wn']
            stim_this_rect = stim[:,self.rectINX]
            brightness = stim_this_rect[frame_no-1]
        
        elif paradigm == 'ssvep':
            brightness = 0.5 + 0.5 * math.sin( 2 * math.pi * self.frequency /self.fs * frame_no + self.start_phase )
        
        return brightness

    def covert2psycho(self,x_res = 1920, y_res = 1080):
        width = self.rect_size/2
        x,y = self.site_point
        x = x-x_res/2 + width
        y = y-y_res/2 + width

        return [x,y]

