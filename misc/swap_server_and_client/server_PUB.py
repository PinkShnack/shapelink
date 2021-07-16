
# https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/patterns/pubsub.html

import zmq
import random
import time

context = zmq.Context.instance()
socket = context.socket(zmq.PUB)

socket.bind("tcp://*:6668")

while True:
    code = "event_code"
    # messagedata = random.randrange(1, 215) - 80
    # code = "A"
    messagedata = "data"
    # print(f"{code}, {messagedata}")
    socket.send_string(f"{code}, {messagedata}")
    # time.sleep(0.5)
