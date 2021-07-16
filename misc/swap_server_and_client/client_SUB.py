
# https://learning-0mq-with-pyzmq.readthedocs.io/en/latest/pyzmq/patterns/pubsub.html

import zmq
import time

context = zmq.Context.instance()
socket = context.socket(zmq.SUB)

socket.connect("tcp://localhost:6668")

topicfilter = "event_code"
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

print("Receiving data from Server...")

# initalize variables, otherwise first time measurement is too long
# because variables are initalized there
counter = 0
time_sum = 0
time1 = 0.0
time2 = 0.0

# for i in range(10):
while True:
    time1 = time.time_ns()
    ret = socket.recv_string()
    time2 = time.time_ns()
    # calculation of mean value
    counter += 1
    dt_us = (time2 - time1)
    time_sum += dt_us
    print("Times: ", time1, time2, dt_us)
    print(
        "ZMQ: sent: ! received: ",
        ret,
        " in ",
        dt_us,
        " ns, mean: ",
        time_sum /
        counter)
    # time.sleep(0.5)

    # topic, messagedata = data.split()
    # print(topic, messagedata)

