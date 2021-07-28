
import zmq
import time
import random
from threading import Thread

context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REP)

socket_RR.bind("tcp://*:6667")

running = True
c = 0
sleep_time = 0.5


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
        time.sleep(sleep_time)


while running:
    c += 1
    print(f"{c}")
    r = socket_RR.recv_string()

    if r == "feats code":  # number code
        socket_RR.send_string("Please send the feats")
        feats = socket_RR.recv_string()
        print(f"Pretend feats: {feats.split(' ')}")
        socket_RR.send_string("feats received")

    elif r == "params code":
        socket_RR.send_string("Here are the params")
        # ACK_params = socket_RR.recv_string()

    elif r == "event code":
        # to be done in another thread
        pub_thread = Thread(target=publisher_thread)
        pub_thread.daemon = True
        pub_thread.start()

        # in current thread, simulate some time
        # used to send data
        time.sleep(sleep_time*20)
        end_data_transfer = "Data Transfer Finished"
        socket_RR.send_string(end_data_transfer)
        print(end_data_transfer)

    elif r == "end code":
        print("Finishing...")
        socket_RR.send_string("Finishing and Closing")
        running = False

    else:
        raise ValueError("bad code")
