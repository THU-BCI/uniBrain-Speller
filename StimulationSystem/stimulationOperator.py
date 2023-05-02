import datetime


class StimulationState:
    def __init__(self):
        self.status = None

class stimulationOperator:
    def __init__(self):
        print("Initialized Stimulation Operator")
        self.messenger = None
        self.state = StimulationState()
        self.events = ['CTOK',
                       'TROK',
                       'TNOK',
                       'RSLT',
                       'EXIT']

    def do_CTOK(self,event):
        self.state.status = 'CTOK'
        message = event.message
        print('接收消息{0}，设置监视器状态{1}\n'.format('CTOK', self.state.status))

    def do_TROK(self, event):
        self.state.status = 'TROK'
        message = event.message
        print('接收消息{0}，设置监视器状态{1}\n'.format('TROK', self.state.status))

    def do_TNOK(self, event):
        self.state.status = 'TNOK'
        message = event.message
        print('接收消息{0}，设置监视器状态{1}\n'.format('TNOK', self.state.status))

    def do_RSLT(self, event):
        message = event.message
        message_result = message['result']

        epochINX = self.controller.currentEpochINX
        cue = self.controller.cueId
        self.controller.currentProcess.change(message_result)
        
        print()
        print('Time now {}:'.format(datetime.datetime.now()))
        print('The result for epoch %s, cue is %d, received identification as %d.' % (epochINX, cue + 1, message_result))

        # 当前反馈结果
        
    def do_EXIT(self, event):
        # 退出程序
        pass

    def add_listener(self, event_manager):
        event_manager.AddEventListener('CTOK', self.do_CTOK)
        event_manager.AddEventListener('TROK', self.do_TROK)
        event_manager.AddEventListener('TNOK', self.do_TNOK)
        event_manager.AddEventListener('RSLT', self.do_RSLT)
        event_manager.AddEventListener('EXIT', self.do_EXIT)


    def remove_listener(self, event_manager):
        event_manager.RemoveEventListener('CTOK', self.do_CTOK)
        event_manager.RemoveEventListener('TROK', self.do_TROK)
        event_manager.RemoveEventListener('TNOK', self.do_TNOK)
        event_manager.RemoveEventListener('RSLT', self.do_RSLT)
        event_manager.RemoveEventListener('EXIT', self.do_RSLT)
