
import abc

import zmq
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.ps_threads import subscriber_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_read_array


class EventData:
    def __init__(self):
        self.id = -1
        self.scalars = list()
        self.traces = list()
        self.images = list()


class ShapeLinkPlugin(abc.ABC):
    def __init__(self,
                 destination="tcp://localhost:6667",
                 verbose=False):
        self.context_rr = zmq.Context.instance()
        self.socket_rr = self.context_rr.socket(zmq.REQ)
        # self.socket.RCVTIMEO = 5000
        # self.socket.SNDTIMEO = 5000
        self.socket_rr.connect(destination)
        # other attributes
        self.scalar_len = 0
        self.vector_len = 0
        self.image_len = 0
        self.image_names = []
        self.image_shape = None
        self.image_shape_len = 2
        self.registered = False
        self.response = list()
        self.sleep_time = 0.5

    def run_client(self):
        # Connect ps socket
        socket_ps = self.connect_ps_socket()
        # Metadata Transfer
        self.send_features_to_server()
        self.register_parameters()
        # Data Transfer
        self.request_data_transfer(socket_ps)
        # Close Process
        self.end_and_close_transfer()

    def connect_ps_socket(self):
        # request the ps port and id from the server
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ps_socket"])
        self.socket_rr.send(msg)
        # recv the ps port and id from the server
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        ip_address = rcv_stream.readQStringList()
        port_address = rcv_stream.readInt64()
        if len(ip_address) == 1:
            ip_address = ip_address[0]
            ip_address = ip_address.replace('*', 'localhost:')
        else:
            raise ValueError("len(ip_address) != 1,"
                             f"len(ip_address) == {len(ip_address)} instead")
        print(f"ps client connecting to {ip_address}{port_address}")

        # connect up the ps socket
        context_ps = zmq.Context.instance()
        socket_ps = context_ps.socket(zmq.SUB)
        socket_ps.connect(f"{ip_address}{port_address}")
        return socket_ps

    def send_features_to_server(self):
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
        self.socket_rr.send(msg)

        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        r = rcv_stream.readInt64()
        if r == message_ids["MSG_ID_feats_code_reply"]:
            print("Features successfully received by server")
        else:
            raise ValueError("ID code not correct, should be "
                             f"{message_ids['MSG_ID_feats_code_reply']}")

    def register_parameters(self):
        print('\n 1a.2')
        print("Requesting Parameters")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_params_code"])
        self.socket_rr.send(msg)

        eventdata = EventData()

        print("Receiving Parameters...")
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        eventdata.scalars = rcv_stream.readQStringList()
        eventdata.traces = rcv_stream.readQStringList()
        eventdata.images = rcv_stream.readQStringList()
        self.image_shape = qstream_read_array(rcv_stream, np.uint16)
        # image_shape_len = 2
        self.scalar_len = len(eventdata.scalars)
        self.vector_len = len(eventdata.traces)
        self.image_len = len(eventdata.images)
        # print(image_shape_len)
        # print(image_shape)
        # assert image_shape_len == len(image_shape)

        print(" Registered data container formats:")
        print(" scalars:", eventdata.scalars)
        print(" traces:", eventdata.traces)
        print(" images:", eventdata.images)
        print(" image_shape:", self.image_shape)

    def request_data_transfer(self, socket_ps):
        # make sure to start the subscriber before the publisher to
        # not miss data transfer
        # start separate thread for data transfer
        print("\n 2a.")
        print("Starting Subscriber Thread")
        sub_thread = Thread(target=subscriber_thread,
                            args=(socket_ps, ))
        sub_thread.daemon = True
        sub_thread.start()

        # now trigger the publisher thread to start
        print("Requesting Data Transfer")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_events_code"])
        self.socket_rr.send(msg)

        # receive confirmation that the server has completed transfer of all data
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        r = rcv_stream.readInt64()
        if r == message_ids["MSG_ID_events_code_complete"]:
            print("Data transfer complete")
        else:
            raise ValueError("ID code not correct, should be "
                             f"{message_ids['MSG_ID_events_code_complete']}")

    def end_and_close_transfer(self):
        print("\n 2d.")
        print("Prompting End to Process")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_end"])
        self.socket_rr.send(msg)

        # receive confirmation that the s`erver has closed
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        r = rcv_stream.readInt64()
        if r == message_ids["MSG_ID_end_reply"]:
            print("Server closed")
        else:
            raise ValueError("ID code not correct, should be "
                             f"{message_ids['MSG_ID_end_reply']}")

        print("Client closed")


cl = ShapeLinkPlugin()
cl.run_client()
