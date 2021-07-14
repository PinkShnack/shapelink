
import zmq
import time

context = zmq.Context.instance()
socket = context.socket(zmq.REQ)

socket.connect("tcp://localhost:6667")

# send code for "i want to send feats"

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
print(ret.split(" "))
# socket.send_string("params ACK")  # number code

print("Starting Events")
new_event = "New event"
while new_event == "New event":
    socket.send_string("event code")
    data = socket.recv_string()
    time.sleep(0.5)
    print(data)
    # do your thing with the data here
    if data == "Data Finished":
        new_event = data

# for i in range(10):  # length of the dataset?
#     time.sleep(0.5)
#     socket.send_string("event code")  # number code
#     ret = socket.recv_string()
#     print(ret.split(" "))


socket.send_string("end code")  # number code
ret = socket.recv_string()
print(ret)








