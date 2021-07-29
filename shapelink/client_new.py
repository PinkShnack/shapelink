
import zmq
import time
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.PS_threads import subscriber_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_read_array
from shapelink.feat_util import map_requested_features_to_defined_features




context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REQ)

socket_RR.connect("tcp://localhost:6667")

sleep_time = 0.5


# setup data streams
send_data = QtCore.QByteArray()
send_stream = QtCore.QDataStream(send_data, QtCore.QIODevice.WriteOnly)


class EventData:
    def __init__(self):
        self.id = -1
        self.scalars = list()
        self.traces = list()
        self.images = list()

# Metadata steps
# Ask if the server is ready for the chosen features


def send_features_to_server(send_stream):
    send_stream.writeInt64(message_ids["MSG_ID_feats_code"])

    # send features
    sc_features, tr_features, im_features = ['deform'], ['other'], ['thing']
    feats = list((sc_features, tr_features, im_features))
    assert isinstance(feats, list), "feats is a list"
    assert len(feats) == 3
    # feats must be sent one by one, list of lists doesn't work
    for feat in feats:
        send_stream.writeQStringList(feat)

    socket_RR.send(send_data)

    message = socket_RR.recv()
    rcv = QtCore.QByteArray(message)
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    if r == message_ids["MSG_ID_feats_code_reply"]:
        print("Features successfully received by server")
    else:
        raise ValueError("ID code not correct, should be "
                         f"{message_ids['MSG_ID_feats_code_reply']}")


def register_parameters():
    print('\n')
    print("Registering Parameters")
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(message_ids["MSG_ID_params_code"])
    socket_RR.send(msg)

    message = socket_RR.recv()
    rcv = QtCore.QByteArray(message)
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)

    eventdata = EventData()
    eventdata.scalars = rcv_stream.readQStringList()
    eventdata.traces = rcv_stream.readQStringList()
    eventdata.images = rcv_stream.readQStringList()
    image_shape = qstream_read_array(rcv_stream, np.uint16)
    # image_shape_len = 2
    scalar_len = len(eventdata.scalars)
    vector_len = len(eventdata.traces)
    image_len = len(eventdata.images)
    # print(image_shape_len)
    # print(image_shape)
    # assert image_shape_len == len(image_shape)

    print(" Registered data container formats:")
    print(" scalars:", eventdata.scalars)
    print(" traces:", eventdata.traces)
    print(" images:", eventdata.images)
    print(" image_shape:", image_shape)


send_features_to_server(send_stream)
register_parameters()

'''

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
'''