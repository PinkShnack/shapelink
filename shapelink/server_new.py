
import zmq
import time
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.PS_threads import publisher_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_write_array


context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REP)

socket_RR.bind("tcp://*:6667")

running = True
c = 0


# msg = QtCore.QByteArray()
# msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
# msg_stream.writeInt64(message_ids["MSG_ID_FEATURE_REQ"])


while running:
    c += 1
    print(f"{c}")
    message = socket_RR.recv()
    rcv = QtCore.QByteArray(message)
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    print(r)

    if r == message_ids["MSG_ID_feats_code"]:
        print("Feature code received")
        # receive the features
        print("Receiving features...")
        feats = []
        for i in range(3):
            feat = rcv_stream.readQStringList()
            feats.append(feat)
        # check that the features are correct...
        assert isinstance(feats, list), "feats is a list"
        assert len(feats) == 3

        # reply saying that server has received the features
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_feats_code_reply"])
        socket_RR.send(msg)

    elif r == message_ids["MSG_ID_params_code"]:
        print("\n")
        print("Registering Parameters")
        # maybe have feats saved to the class as a list?
        # wn't get the "feats may be undefined" warning then.
        scalar_reg_features = feats[0]
        vector_reg_features = feats[1]
        image_reg_features = feats[2]
        scalar_len = len(scalar_reg_features)
        vector_len = len(vector_reg_features)
        image_len = len(image_reg_features)
        image_names = image_reg_features
        image_shape = np.array([80, 250])
        image_shape_len = len(image_shape)

        # prepare message in byte stream
        # send parameters
        print("Sending Parameters")

        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList(scalar_reg_features)
        msg_stream.writeQStringList(vector_reg_features)
        msg_stream.writeQStringList(image_reg_features)
        qstream_write_array(msg_stream, image_shape)
        socket_RR.send(msg)

    elif r == message_ids["MSG_ID_events_code"]:
        print("\n")
        print("Starting Publisher Thread")
        pub_thread = Thread(target=publisher_thread)
        pub_thread.daemon = True
        pub_thread.start()

        # in current thread, simulate some time used to send data
        print("Sending data...")
        time.sleep(10)

        # reply saying that server has completed transfer of all data
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_events_code_complete"])
        socket_RR.send(msg)

    elif r == message_ids["MSG_ID_end"]:
        print("\n")
        print("Ending and Closing")
        # stop the while loop after exciting this elif statement
        running = False

        # confirm that the server is closing
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_end_reply"])
        socket_RR.send(msg)

        print("Server closed")

        # break
    else:
        raise ValueError("Did not understand message received from Client: "
                         f"{r}")
