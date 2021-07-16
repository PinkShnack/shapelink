
import zmq
import time
from threading import Thread

context = zmq.Context.instance()
socket = context.socket(zmq.REQ)

socket.connect("tcp://localhost:6667")


def subscriber_thread():
    # start separate thread
    context = zmq.Context.instance()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:6668")
    topicfilter = "A"
    socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

    while True:
        data = socket.recv_string()
        topic, messagedata = data.split()
        print(messagedata)

# Ask if the server is ready for the chosen features
socket.send_string("feats code")  # number code
time.sleep(0.5)
ret = socket.recv_string()
if ret == "Please send the feats":
    socket.send_string("Here is a list of feats")  # number code
    time.sleep(0.5)
    confirm = socket.recv_string()
    print(confirm)

print("Starting Params")
time.sleep(1)

socket.send_string("params code")  # number code
ret = socket.recv_string()
time.sleep(0.5)
print(f"Pretend params: {ret.split(' ')}")


# make sure to start the subscriber before the publisher to
# not miss data transfer

# start separate thread
sub_thread = Thread(target=subscriber_thread)
sub_thread.daemon = True
sub_thread.start()

# will trigger publisher thread to start
print("Starting Data Transfer")
socket.send_string("event code")


# When server is finished sending data, it should send a message via the
# REP socket. This is simulated here:
end_data_transfer = socket.recv_string()
if end_data_transfer == "Data Transfer Finished":
    print(end_data_transfer)

    socket.send_string("end code")  # number code
    ret = socket.recv_string()
    print(ret)
else:
    raise ValueError(f"The received message was not '{end_data_transfer}'")
