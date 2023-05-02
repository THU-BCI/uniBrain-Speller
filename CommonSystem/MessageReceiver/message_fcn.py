from CommonSystem.MessageReceiver.EventManager import Event
import time


def operate_fcn(message_queue, event_manager, stop):
    while True:
        if message_queue.qsize() > 0:
            message = message_queue.get()
            if len(message) > 4:
                event = Event(type_=message[0:4])
                result = int(message[5:])
            else:
                event = Event(type_=message)
                result = 0
            event.message = {'result': result}
            event_manager.SendEvent(event)
        if stop():
            print("Exiting operate_exchange_message_fcn!")
            break
        time.sleep(0.1)


def receive_fcn(message_queue, socket, stop):
    # 循环接收消息
    BUFIZ = 1024
    socket.settimeout(20000)
    while True:
        # 收信方法调用，当消费者在0.5s时限内能收到的消息时，consumeMsg为bytes()型，本例仅使用str()方法给出简单的反序列化示例，具体反序列化
        # 方法应由使用者决定
        consumeMsg = socket.recv(BUFIZ)
        if consumeMsg:
            message_queue.put(str(consumeMsg)[2:-1])
            print(str(consumeMsg)[2:-1])
            if(str(consumeMsg)[2:-1] == "EXIT"):
                break
        time.sleep(0.1)
        if stop():
            print("Exiting receive_exchange_message_fcn!")
            break