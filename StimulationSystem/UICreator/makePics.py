
import sys
sys.path.append('.')
sys.path.append('..')
from stiConfig import stiConfig
from UIFactory import UIFactory

for p in ['ssvep']:
    config = stiConfig(paradigm=p)
    factory = UIFactory(config)
    frames = factory.getFrames()
    factory.saveFrames(frames)

