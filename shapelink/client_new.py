
import zmq
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.PS_threads import subscriber_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_read_array


context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REQ)

socket_RR.connect("tcp://localhost:6667")

sleep_time = 0.5


class EventData:
    def __init__(self):
        self.id = -1
        self.scalars = list()
        self.traces = list()
        self.images = list()


def send_features_to_server():
    # send features
    # features defined by user plugin `choose_features`
    sc_features, tr_features, im_features = ['deform'], ['other'], ['thing']
    feats = list((sc_features, tr_features, im_features))
    assert isinstance(feats, list), "feats is a list"
    assert len(feats) == 3

    print("\n 1a.1")
    print("Sending Features code")
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(message_ids["MSG_ID_feats_code"])
    # feats must be sent one by one, list of lists doesn't work
    print("Sending Features")
    for feat in feats:
        msg_stream.writeQStringList(feat)
    socket_RR.send(msg)

    rcv = QtCore.QByteArray(socket_RR.recv())
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    if r == message_ids["MSG_ID_feats_code_reply"]:
        print("Features successfully received by server")
    else:
        raise ValueError("ID code not correct, should be "
                         f"{message_ids['MSG_ID_feats_code_reply']}")


def register_parameters():
    print('\n 1a.2')
    print("Requesting Parameters")
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(message_ids["MSG_ID_params_code"])
    socket_RR.send(msg)

    eventdata = EventData()

    print("Receiving Parameters...")
    rcv = QtCore.QByteArray(socket_RR.recv())
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
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


def request_data_transfer():

    # make sure to start the subscriber before the publisher to
    # not miss data transfer
    # start separate thread for data transfer
    print("\n 2a.")
    print("Starting Subscriber Thread")
    sub_thread = Thread(target=subscriber_thread)
    sub_thread.daemon = True
    sub_thread.start()

    # now trigger the publisher thread to start
    print("Requesting Data Transfer")
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(message_ids["MSG_ID_events_code"])
    socket_RR.send(msg)

    # receive confirmation that the server has completed transfer of all data
    rcv = QtCore.QByteArray(socket_RR.recv())
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    if r == message_ids["MSG_ID_events_code_complete"]:
        print("Data transfer complete")
    else:
        raise ValueError("ID code not correct, should be "
                         f"{message_ids['MSG_ID_events_code_complete']}")


def end_and_close_transfer():

    print("\n 2d.")
    print("Prompting End to Process")
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(message_ids["MSG_ID_end"])
    socket_RR.send(msg)

    # receive confirmation that the server has closed
    rcv = QtCore.QByteArray(socket_RR.recv())
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    if r == message_ids["MSG_ID_end_reply"]:
        print("Server closed")
    else:
        raise ValueError("ID code not correct, should be "
                         f"{message_ids['MSG_ID_end_reply']}")

    print("Client closed")


# Metadata Transfer
send_features_to_server()
register_parameters()
# Data Transfer
request_data_transfer()
# Close Process
end_and_close_transfer()
