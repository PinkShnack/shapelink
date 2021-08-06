
import zmq
import time
import random


def subscriber_thread(socket):
    # start separate thread

    topicfilter = "A"
    socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

    while True:
        data = socket.recv_string()
        # run the plugin run_event_message then handle_event
        # which will execute your custom plugin
        topic, messagedata = data.split()
        print(messagedata)


def publisher_thread(socket):
    # to be done in another thread
    # this initial connection should not be done here. What if there
    # is a connection issue at this point? Makes the initial metadata
    # transfer useless

    while True:
        code = "A"
        event_id = random.randint(1, 10)
        messagedata = f"data_{event_id}"
        socket.send_string(f"{code}, {messagedata}")
        time.sleep(0.5)
