
import zmq
import time
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.ps_threads import publisher_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_write_array


context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REP)
# The RR port number should be four digits long
bind_to = 'tcp://*:6667'
socket_RR.bind(bind_to)

running = True


while running:
    message = socket_RR.recv()
    rcv = QtCore.QByteArray(message)
    rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
    r = rcv_stream.readInt64()
    print(r)

    if r == message_ids["MSG_PS_socket"]:
        # connect up the PS socket
        print("PS server binding...")
        context = zmq.Context.instance()
        socket_PS = context.socket(zmq.PUB)
        ip_address = bind_to[:-5]
        port_address = socket_PS.bind_to_random_port(ip_address)
        print(f"PS server bound to {ip_address}:{port_address}")
        # send the port_address to the client
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList([ip_address])
        msg_stream.writeInt64(port_address)
        socket_RR.send(msg)

    elif r == message_ids["MSG_ID_feats_code"]:
        print("\n 1b.1")
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
        print("\n 1b.2")
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
        print("\n 2b.")
        print("Starting Publisher Thread")
        pub_thread = Thread(target=publisher_thread,
                            args=(socket_PS, ))
        pub_thread.daemon = True
        pub_thread.start()

        # in current thread, simulate some time used to send data
        print("Sending data...")
        time.sleep(10)

        # reply saying that server has completed transfer of all data
        print("\n 2c.")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_events_code_complete"])
        socket_RR.send(msg)

    elif r == message_ids["MSG_ID_end"]:
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
