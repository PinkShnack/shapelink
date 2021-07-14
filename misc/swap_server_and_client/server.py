import zmq
import random

context = zmq.Context.instance()
socket = context.socket(zmq.REP)

socket.bind("tcp://*:6667")

running = True
length_dataset = 10

while running:
    r = socket.recv_string()

    if r == "feats code":  # number code
        socket.send_string("Please send the feats")
        feats = socket.recv_string()
        print(feats.split(" "))
        socket.send_string("feats received")

    elif r == "params code":
        socket.send_string("Here are the params")
        # ACK_params = socket.recv_string()
    elif r == "end code":
        print("Finishing")
        socket.send_string("Finishing")
        running = False

    elif r == "event code":
        # should have a SUB PUB thing here then...
        # randomly stop the sending to simulate a
        # limited number of events
        event_id = random.randint(5, 11)
        if event_id < length_dataset:
            socket.send_string(
                "Here is the data for data")
        else:
            socket.send_string(
                "Data Finished")

    else:
        raise ValueError("bad code")

