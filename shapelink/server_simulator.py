
import zmq
from PySide2 import QtCore
import numpy as np

from .ps_threads import publisher_thread
from .msg_def import message_ids
from .util import qstream_write_array


class ServerSimulator:
    def __init__(self,
                 simulator_path=None,
                 bind_to='tcp://*:6667',
                 random_port=False,
                 verbose=False):
        self._bind_to_socket_rr(bind_to, random_port)
        # other attributes
        self.verbose = verbose
        if self.verbose:
            print(" Init Server Simulator")
            print(f" Bind to: {self.ip_address_rr}:{self.port_address_rr}")
        self.feats = []
        self.scalar_len = 0
        self.vector_len = 0
        self.image_len = 0
        self.image_names = []
        self.image_shape = None
        self.image_shape_len = 2
        self.registered = False
        self._first_call = True
        self.running = True
        # ps attributes
        self.port_address_ps = None
        self.ip_address_ps = None
        self.context_ps = None
        self.socket_ps = None
        # path to data
        self.simulator_path = simulator_path

    def _bind_to_socket_rr(self, bind_to, random_port):
        self.context_rr = zmq.Context.instance()
        self.socket_rr = self.context_rr.socket(zmq.REP)
        # self.socket_rr.RCVTIMEO = 5000
        # self.socket_rr.SNDTIMEO = 5000
        # The rr port number should be four digits long if not random
        self.ip_address_rr = bind_to[:-5]
        self.port_address_rr = bind_to[-4:]
        if random_port:
            self.port_address_rr = self.socket_rr.bind_to_random_port(
                self.ip_address_rr)
        else:
            self.socket_rr.bind(bind_to)

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
                self.start_publisher()
                self.data_transfer_complete()

            elif r == message_ids["MSG_ID_end"]:
                self.close_process()

            else:
                raise ValueError(
                    f"Did not understand message received from Client: {r}")

    def receive_request_from_client(self):
        if self._first_call:   # needed for accurate line_profiler tests
            try:
                message = self.socket_rr.recv()
                rcv = QtCore.QByteArray(message)
            except zmq.error.ZMQError:
                if self.verbose:
                    print("ZMQ Error")
                return
            self._first_call = False
        else:
            try:
                message = self.socket_rr.recv()
                rcv = QtCore.QByteArray(message)
            except zmq.error.ZMQError:
                if self.verbose:
                    print("ZMQ Error")
                return

        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        r = rcv_stream.readInt64()
        if self.verbose:
            print(f"Request code received: {r}")
        return r, rcv_stream

    def connect_ps_socket(self):
        """Bind to the Publisher-subscriber socket"""
        self.context_ps = zmq.Context.instance()
        self.socket_ps = self.context_ps.socket(zmq.PUB)
        self.port_address_ps = self.socket_ps.bind_to_random_port(
            self.ip_address_rr)
        if self.verbose:
            print("PUB-SUB socket bound to "
                  f"{self.ip_address_rr}:{self.port_address_ps}")
        # send the port_address to the client
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList([self.ip_address_rr])
        msg_stream.writeInt64(self.port_address_ps)
        self._send_msg_info(msg)

    def _send_msg_info(self, msg):
        try:
            if self.verbose:
                print("Send msg info")
            self.socket_rr.send(msg)
        except zmq.error.ZMQError:
            if self.verbose:
                print("ZMQ Error")
            return

    def receive_features(self, rcv_stream):
        """Receive the features"""
        if self.verbose:
            print("Receiving features...")
        for i in range(3):
            feat = rcv_stream.readQStringList()
            self.feats.append(feat)
        # check that the features are correct
        assert isinstance(self.feats, list), "feats is a list"
        assert len(self.feats) == 3
        if len([i for sublist in self.feats for i in sublist]) == 0:
            raise ValueError("Feature list received from Plugin is empty")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_feats_code_reply"])
        self._send_msg_info(msg)

    def register_parameters(self,
                            scalar_reg_features=None,
                            vector_reg_features=None,
                            image_reg_features=None,
                            image_shape=None,
                            settings_names=None,
                            settings_values=None):
        """Register parameters that are sent to other processes"""
        if self.verbose:
            print("Registering Parameters")
        if settings_values is None:
            settings_values = []
        if settings_names is None:
            settings_names = []
        if scalar_reg_features is None:
            scalar_reg_features = self.feats[0]
        if vector_reg_features is None:
            vector_reg_features = self.feats[1]
        if image_reg_features is None:
            image_reg_features = self.feats[2]
        if image_shape is None:
            # should send image shape from server to client and include it
            # as a EventData attribute so it can be returned to plugin
            # for analysis
            image_shape = np.array([80, 250], dtype=np.uint16)
        assert len(settings_values) == len(
            settings_names), "Mismatch setting names and values"

        self.scalar_len = len(scalar_reg_features)
        self.vector_len = len(vector_reg_features)
        self.image_len = len(image_reg_features)
        self.image_names = image_reg_features
        self.image_shape = image_shape
        self.image_shape_len = len(image_shape)
        if self.verbose:
            print("Sending Parameters")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeQStringList(scalar_reg_features)
        msg_stream.writeQStringList(vector_reg_features)
        msg_stream.writeQStringList(image_reg_features)
        qstream_write_array(msg_stream, self.image_shape)
        self._send_msg_info(msg)
        self.registered = True

    def start_publisher(self):
        if self.verbose:
            print("Starting Publisher")
        publisher_thread(self)

    def data_transfer_complete(self):
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_events_code_complete"])
        self._send_msg_info(msg)

    def close_process(self):
        # stop the while loop after exciting this elif statement
        self.running = False
        # confirm that the server is closing
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_end_reply"])
        self._send_msg_info(msg)
        if self.verbose:
            print("Server closing")


def start_simulator(simulator_path, verbose=False):
    s = ServerSimulator(simulator_path=simulator_path, verbose=verbose)
    s.run_server()
