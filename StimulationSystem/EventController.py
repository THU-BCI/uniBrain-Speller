from time import time
from psychopy import parallel
import time

class EventController():
    def __init__(self, COM='3100') -> None:
        # hex 2 dec
        self.address = int(COM, 16)
        self.port = parallel.ParallelPort(self.address)
        self.clearEvent()

    def sendEvent(self, eventType):
        self.port.setData(eventType)
        
    def clearEvent(self):
        self.port.setData(0)
        self.port.setData(0)
        time.sleep(0.01)


if __name__ =='__main__':
    import numpy as np
    
    s = [i+1 for i in range(160)]
    np.random.shuffle(s)
    e = EventController(COM='5EFC')
    for j in range(3):
        for inx,i in enumerate(s):
            print('send %s: [%s]' %(inx,i))
            e.sendEvent(i)  
            time.sleep(0.5)
            e.clearEvent()
            
            # e.clearEvent()
            if (inx+1)%5==0:
                time.sleep(1)