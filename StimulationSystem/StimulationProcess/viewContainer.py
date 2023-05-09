class viewContainer():
    """
    The viewContainer class contains all the elements required for the presentation of stimuli. They will be transfered to all the processes.
    
    Attributes:
        w: The window object where all stimuli are displayed.
        initFrame: The initial frame displayed when not in a stimulation state.
        frameSet: A set of ImageStim objects representing the stimulation frames.
        cue: An array of cue indices.
        targetPos: The positions of the targets on the screen, used when displaying cues.
        stringPos: The positions of the characters during online experiments (currently unused).
        cueTime: The duration of cue display.
        MODE: The run mode.
        sync_mode: The synchronization mode.
        key_list: The list of keys used for input.
        strideText: The stride text.
        twoPhaseBox: The two-phase box.
        
    Methods:
        __init__(config): Initializes the viewContainer instance with the given config.
        takeConfig(config): Configures the viewContainer instance with the given config.
    """
    def __init__(self, config) -> None:

        # The window object where all stimuli are displayed.
        self.w = None
        # The initial frame displayed when not in a stimulation state.
        self.initFrame = None
        # A set of ImageStim objects representing the stimulation frames.
        self.frameSet = None
        # An array of cue indices.
        self.cue = None
        # The positions of the targets on the screen, used when displaying cues.
        self.targetPos = None
        # The positions of the characters during online experiments (currently unused).
        self.stringPos = None
        self.cueTime = None
        
        # Run mode.
        self.MODE = None
        self.sync_mode = None
        self.key_list = None
        
        self.strideText = None
        self.twoPhaseBox = None

        self.takeConfig(config)

    def takeConfig(self, config):

        self.paradigm = config.paradigm
        # Cue indices.
        self.cueIndices = config.cueIndices
        # Cue events.
        self.cueEvents = config.cueEvents
        # Corresponding characters.
        self.char = config.char
        
        self.events = config.events
        self.targetNUM = config.targetNUM
        self.blockNUM = config.blockNUM
        # Displayed characters.
        self.displayChar = config.displayChar
        self.resolution = config.resolution
        self.cueTime = config.cueTime
        self.cubicSize = config.cubicSize

        self.COM = config.COM
        self.MODE = config.MODE
        self.sync_mode = config.sync_mode
        
        self.key_list = config.key_list

