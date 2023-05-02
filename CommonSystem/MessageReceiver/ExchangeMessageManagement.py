import queue
from threading import Thread
import threading
import uuid
import socket
from CommonSystem.MessageReceiver.EventManager import EventManager, Event
from CommonSystem.MessageReceiver.message_fcn import operate_fcn,receive_fcn

class ExchangeMessageManagement:
    def __init__(self,role,exchange_message_operator,config):


        # role 决定了当前程序在TCP/IP中承担什么角色：server/client
        self.role = role

        self.receive_message_thread = None
        self.operator_message_thread = None
        self.message_queue = None
        self.exchange_message_operator = exchange_message_operator

        self.event_manager = EventManager(self.role)

        self.hostname = config.host_ip
        self.port = config.host_port

        self.initial(exchange_message_operator)

        self.stop_flag = False

    def connect(self):
        """
        try to connect data server
        """
        # 开启信息交换监听功能
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        notconnect = True
        reconnecttime = 0  # 未连接次数
        while notconnect:
            if self.role == 'server':
                try:
                    self.sock.bind(('', self.port))
                    self.sock.listen(1)
                    print('Server wating for connection')
                    self.clientSocket, clientAddr = self.sock.accept()
                    notconnect = False
                except:
                    reconnecttime += 1
                    if reconnecttime > 5:
                        break
            elif self.role == 'client':
                try:
                    self.sock.connect((self.hostname, self.port))
                    self.clientSocket = self.sock
                    notconnect = False
                except:
                    reconnecttime += 1
                    if reconnecttime > 5:
                        break

            print('TCP/IP communication is available now.')

        self.shutdown_flag = threading.Event()
        self.shutdown_flag.set()
        self.sock.setblocking(True)
        # set buffer size（通道数*采样点*采样时间*float字节数）
        return notconnect

    def initial(self, exchange_message_operator):

        if self.connect():
            raise Exception('Not connected,check client or ip address')
        else:
            self.exchange_message_operator = exchange_message_operator
            self.message_queue = queue.Queue(0)
            self.state = exchange_message_operator.state

            if self.event_manager.count != 0:
                self.remove_listener_from_operator()

            self.add_listener_from_operator()

            self.receive_message_thread = Thread(name=self.role+' '+'receive',target=receive_fcn, args=(self.message_queue, self.clientSocket, lambda: self.stop_flag,))

            self.operator_message_thread = Thread(name=self.role+' '+'operate',target=operate_fcn, args=(self.message_queue, self.event_manager, lambda: self.stop_flag,))
            self.event_manager.Start()

    def start(self):
        self.receive_message_thread.start()
        self.operator_message_thread.start()

    def stop(self):
        self.stop_flag = True
        self.event_manager.Stop()
        self.operator_message_thread.join()
        self.receive_message_thread.join()  # 设置超时时间为 5 秒
        # if self.receive_message_thread.is_alive():
        #     print("Force stopping receive_message_thread")
        #     self.receive_message_thread.()
    def stop_for_operate(self):
        self.stop_flag = True
        self.event_manager.Stop()
        self.operator_message_thread.join()
        self.receive_message_thread.join()  # 设置超时时间为 5 秒
        


    def delete(self):
        self.remove_listener_from_operator()

    def send_exchange_message(self, message):
        self.clientSocket.send(message.encode('utf-8'))
        # print('send '+ message +'!')

    def add_listener_from_operator(self):
        self.exchange_message_operator.add_listener(self.event_manager)

    def remove_listener_from_operator(self):
        self.exchange_message_operator.remove_listener(self.event_manager)

