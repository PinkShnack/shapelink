
import zmq
import time
from threading import Thread

context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REQ)

socket_RR.connect("tcp://localhost:6667")

sleep_time = 0.5


def subscriber_thread():
    # start separate thread
    context_PS = zmq.Context.instance()
    socket_PS = context_PS.socket(zmq.SUB)
    socket_PS.connect("tcp://localhost:6668")
    topicfilter = "A"
    socket_PS.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

    while True:
        data = socket_PS.recv_string()
        topic, messagedata = data.split()
        print(messagedata)

# Ask if the server is ready for the chosen features
socket_RR.send_string("feats code")  # number code
time.sleep(sleep_time)
ret = socket_RR.recv_string()
if ret == "Please send the feats":
    socket_RR.send_string("Here is a list of feats")  # number code
    time.sleep(sleep_time)
    confirm = socket_RR.recv_string()
    print(confirm)

print("Starting Params")
time.sleep(sleep_time)

socket_RR.send_string("params code")  # number code
ret = socket_RR.recv_string()
print(f"Pretend params: {ret.split(' ')}")
time.sleep(sleep_time)

# make sure to start the subscriber before the publisher to
# not miss data transfer

# start separate thread for data transfer
sub_thread = Thread(target=subscriber_thread)
sub_thread.daemon = True
sub_thread.start()

# now trigger the publisher thread to start
print("Starting Data Transfer")
socket_RR.send_string("event code")


# When server is finished sending data, it should send a message via the
# REP socket_RR. This is simulated here:
end_data_transfer = socket_RR.recv_string()
if end_data_transfer == "Data Transfer Finished":
    print(end_data_transfer)

    socket_RR.send_string("end code")  # number code
    ret = socket_RR.recv_string()
    print(ret)
else:
    raise ValueError(f"The received message was not '{end_data_transfer}'")
