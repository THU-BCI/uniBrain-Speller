class viewContainer():
    # container 应该包含所有刺激所需的要素
    def __init__(self, config) -> None:

        # w 代表window,所有的刺激都要在win上显示
        self.w = None
        # initFrame代表初始帧,非刺激状态下都是这一帧
        self.initFrame = None
        # frameSet是ImageStim的集合,是刺激帧
        self.frameSet = None
        # cue应该是一串数组
        self.cue = None
        # targetPos是每个目标在屏幕上的位置,显示cue的时候用得到
        self.targetPos = None
        # stringPos是在线实验时候,字符的位置,暂时用不到
        self.stringPos = None
        self.cueTime = None
        
        
        # run mode
        self.MODE = None
        self.sync_mode = None
        # self.twoPhaseRectPos = None
        # self.strideTextPos = None
        self.key_list = None
        
        self.strideText = None
        self.twoPhaseBox = None
        

        self.takeConfig(config)
        pass

    def takeConfig(self, config):

        self.paradigm = config.paradigm
        # 索引
        self.cueIndices = config.cueIndices
        # 标签
        self.cueEvents = config.cueEvents
        # 对应字符
        self.char = config.char
        
        self.events = config.events
        self.targetNUM = config.targetNUM
        self.blockNUM = config.blockNUM
        # 显示的字符
        self.displayChar = config.displayChar
        self.resolution = config.resolution
        self.cueTime = config.cueTime
        self.cubicSize = config.cubicSize

        self.COM = config.COM
        self.MODE = config.MODE
        self.sync_mode = config.sync_mode
        
    
        # self.twoPhaseRectPos =  config.twoPhaseRectPos
        # self.strideTextPos = config.strideTextPos
        
        self.key_list = config.key_list
        pass
