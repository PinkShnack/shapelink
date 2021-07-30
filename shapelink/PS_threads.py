
import zmq
import time
import random


def subscriber_thread():
    # start separate thread
    context_PS = zmq.Context.instance()
    socket_PS = context_PS.socket(zmq.SUB)
    socket_PS.connect("tcp://localhost:6668")
    topicfilter = "A"
    socket_PS.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

    while True:
        data = socket_PS.recv_string()
        # run the plugin run_event_message then handle_event
        # which will execute your custom plugin
        topic, messagedata = data.split()
        print(messagedata)


def publisher_thread():
    # to be done in another thread
    # this initial connection should not be done here. What if there
    # is a connection issue at this point? Makes the initial metadata
    # transfer useless
    context = zmq.Context.instance()
    socket_PS = context.socket(zmq.PUB)
    socket_PS.bind("tcp://*:6668")
    while True:
        code = "A"
        event_id = random.randint(1, 10)
        messagedata = f"data_{event_id}"
        socket_PS.send_string(f"{code}, {messagedata}")
        time.sleep(0.5)