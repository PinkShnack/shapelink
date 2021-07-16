import zmq
import time
import random
from threading import Thread

context = zmq.Context.instance()
socket = context.socket(zmq.REP)

socket.bind("tcp://*:6667")

running = True
c = 0


def publisher_thread():
    # to be done in another thread
    context = zmq.Context.instance()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:6668")
    while True:
        code = "A"
        event_id = random.randint(1, 10)
        messagedata = f"data_{event_id}"
        socket.send_string(f"{code}, {messagedata}")
        time.sleep(0.5)

while running:
    c += 1
    print(f"{c}")
    r = socket.recv_string()

    if r == "feats code":  # number code
        socket.send_string("Please send the feats")
        feats = socket.recv_string()
        print(f"Pretend feats: {feats.split(' ')}")
        socket.send_string("feats received")

    elif r == "params code":
        socket.send_string("Here are the params")
        # ACK_params = socket.recv_string()

    elif r == "event code":
        # to be done in another thread
        pub_thread = Thread(target=publisher_thread)
        pub_thread.daemon = True
        pub_thread.start()

        # in current thread, simulate some time
        # used to send data
        time.sleep(10)
        end_data_transfer = "Data Transfer Finished"
        socket.send_string(end_data_transfer)
        print(end_data_transfer)

    elif r == "end code":
        print("Finishing...")
        socket.send_string("Finishing and Closing")
        running = False

    else:
        raise ValueError("bad code")
