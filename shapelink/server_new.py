
import zmq
import time
from threading import Thread
from PySide2 import QtCore

from shapelink.PS_threads import subscriber_thread
from shapelink.msg_def import message_ids


context_RR = zmq.Context.instance()
socket_RR = context_RR.socket(zmq.REP)

socket_RR.bind("tcp://*:6667")

running = True
c = 0
sleep_time = 0.5

# setup data streams
send_data = QtCore.QByteArray()
send_stream = QtCore.QDataStream(send_data, QtCore.QIODevice.WriteOnly)

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

    if r == message_ids["MSG_ID_feats_code"]:
        print("Feature code received")
        send_stream.writeInt64(message_ids["MSG_ID_feats_code_reply"])
        socket_RR.send(send_data)

        print("Receiving features...")
        rcv = QtCore.QByteArray(socket_RR.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        print("rcv stream ready")
        # failing here for some reason
        feats = []
        for i in range(3):
            feats.append(rcv_stream.readQStringList())
        if len([i for sublist in feats for i in sublist]) == 0:
            # if self.verbose:
            #     print("Feature Request List Empty")
            # feats = None
            raise ValueError("feats list is empty!")
        assert len(feats) == 3
        # some basic checks that will not be kept
        assert len(feats[0]) == 1
        assert feats[0] == ["deform"]
        print("Features received")
        send_stream.writeInt64(message_ids["MSG_ID_feats_received_reply"])
        socket_RR.send(send_data)


'''
    elif r == "params code":
        socket_RR.send_string("Here are the params")
        # ACK_params = socket_RR.recv_string()

    elif r == "event code":
        # to be done in another thread
        pub_thread = Thread(target=publisher_thread)
        pub_thread.daemon = True
        pub_thread.start()

        # in current thread, simulate some time
        # used to send data
        time.sleep(sleep_time*20)
        end_data_transfer = "Data Transfer Finished"
        socket_RR.send_string(end_data_transfer)
        print(end_data_transfer)

    elif r == "end code":
        print("Finishing...")
        socket_RR.send_string("Finishing and Closing")
        running = False

    else:
        raise ValueError("bad code")
'''