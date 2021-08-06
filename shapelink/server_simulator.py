
import zmq
import time
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.ps_threads import publisher_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_write_array


class ServerSimulator:
    def __init__(self,
                 bind_to='tcp://*:6667',
                 random_port=False,
                 verbose=False):

        self.context_rr = zmq.Context.instance()
        self.socket_rr = self.context_rr.socket(zmq.REP)
        # self.socket_rr.RCVTIMEO = 5000
        # self.socket_rr.SNDTIMEO = 5000
        # The rr port number should be four digits long if not random
        self.ip_address = bind_to[:-5]
        self.port_address = bind_to[-4:]
        if random_port:
            self.port_address = self.socket_rr.bind_to_random_port(
                self.ip_address)
        else:
            self.socket_rr.bind(bind_to)
        # other attributes
        self.verbose = verbose
        if self.verbose:
            print(" Init Server Simulator")
            print(" Bind to: {}:{}".format(self.ip_address, self.port_address))
        self.scalar_len = 0
        self.vector_len = 0
        self.image_len = 0
        self.image_names = []
        self.image_shape = None
        self.image_shape_len = 2
        self.registered = False
        self.response = list()
        self.running = True

    def run_server(self):
        while self.running:
            r, rcv_stream = self.receive_request_from_client()

            if r == message_ids["MSG_ps_socket"]:
                self.connect_ps_socket()

            elif r == message_ids["MSG_ID_feats_code"]:
                self.receive_features(rcv_stream)

            elif r == message_ids["MSG_ID_params_code"]:
                self.register_parameters()

            elif r == message_ids["MSG_ID_events_code"]:
                # sending data is handled in the publisher thread
                self.start_publisher_thread()
                self.data_transfer_complete()

            elif r == message_ids["MSG_ID_end"]:
                self.close_process()

            else:
                raise ValueError(
                    f"Did not understand message received from Client: {r}")

    def receive_request_from_client(self):
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        r = rcv_stream.readInt64()
        print(r)
        return r, rcv_stream

    def connect_ps_socket(self):
        # connect up the ps socket
        print("ps server binding...")
        self.context_ps = zmq.Context.instance()
        self.socket_ps = self.context_ps.socket(zmq.PUB)
        self.port_address_ps = self.socket_ps.bind_to_random_port(
            self.ip_address)
        print("ps server bound to "
              f"{self.ip_address}:{self.port_address_ps}")
        # send the port_address to the client
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList([self.ip_address])
        msg_stream.writeInt64(self.port_address_ps)
        self.socket_rr.send(msg)

    def receive_features(self, rcv_stream):
        print("\n 1b.1")
        print("Feature code received")
        # receive the features
        print("Receiving features...")
        self.feats = []
        for i in range(3):
            feat = rcv_stream.readQStringList()
            self.feats.append(feat)
        # check that the features are correct...
        assert isinstance(self.feats, list), "feats is a list"
        assert len(self.feats) == 3
        # reply saying that server has received the features
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_feats_code_reply"])
        self.socket_rr.send(msg)

    def register_parameters(self):
        print("\n 1b.2")
        print("Registering Parameters")
        scalar_reg_features = self.feats[0]
        vector_reg_features = self.feats[1]
        image_reg_features = self.feats[2]
        self.scalar_len = len(scalar_reg_features)
        self.vector_len = len(vector_reg_features)
        self.image_len = len(image_reg_features)
        self.image_names = image_reg_features
        self.image_shape = np.array([80, 250])
        self.image_shape_len = len(self.image_shape)
        # prepare message in byte stream
        # send parameters
        print("Sending Parameters")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList(scalar_reg_features)
        msg_stream.writeQStringList(vector_reg_features)
        msg_stream.writeQStringList(image_reg_features)
        qstream_write_array(msg_stream, self.image_shape)
        self.socket_rr.send(msg)

    def start_publisher_thread(self):
        print("\n 2b.")
        print("Starting Publisher Thread")
        pub_thread = Thread(target=publisher_thread,
                            args=(self.socket_ps,))
        pub_thread.daemon = True
        pub_thread.start()

    def data_transfer_complete(self):
        # in current thread, simulate some time used to send data
        print("Sending data...")
        time.sleep(10)
        # reply saying that server has completed transfer of all data
        print("\n 2c.")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_events_code_complete"])
        self.socket_rr.send(msg)

    def close_process(self):
        print("Ending and Closing")
        # stop the while loop after exciting this elif statement
        self.running = False
        # confirm that the server is closing
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_end_reply"])
        self.socket_rr.send(msg)
        print("Server closed")


s = ServerSimulator()
s.run_server()
