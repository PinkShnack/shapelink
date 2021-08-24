
import abc

import zmq
from threading import Thread
from PySide2 import QtCore
import numpy as np

from shapelink.ps_threads import subscriber_thread
from shapelink.msg_def import message_ids
from shapelink.util import qstream_read_array
from shapelink.feat_util import map_requested_features_to_defined_features


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
        self.feats = []
        self.reg_features = EventData()
        self.registered = False
        self.response = list()
        self.sleep_time = 0.5
        # ps attributes
        self.port_address_ps = None
        self.ip_address_ps = None
        self.context_ps = None
        self.socket_ps = None

    def run_client(self):
        # Connect ps socket
        self.connect_ps_socket()
        # Metadata Transfer
        self.send_features_to_server()
        self.register_parameters()
        self.after_register()
        # Data Transfer
        self.request_data_transfer()
        self.after_transmission()
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
        ip_address_ps = rcv_stream.readQStringList()
        self.port_address_ps = rcv_stream.readInt64()
        if len(ip_address_ps) == 1:
            ip_address_ps = ip_address_ps[0]
            self.ip_address_ps = ip_address_ps.replace('*', 'localhost:')
        else:
            raise ValueError("len(ip_address) != 1,"
                             f"len(ip_address) == {len(ip_address_ps)} instead")

        print(f"ps client connecting to {self.ip_address_ps}{self.port_address_ps}")

        # connect up the ps socket
        self.context_ps = zmq.Context.instance()
        self.socket_ps = self.context_ps.socket(zmq.SUB)
        self.socket_ps.connect(f"{self.ip_address_ps}{self.port_address_ps}")

    def send_features_to_server(self):
        # send features
        # features defined by user plugin `choose_features`
        # sc_features, tr_features, im_features = ['deform'], ['trace'], ['image']
        # feats = list((sc_features, tr_features, im_features))

        user_feats = self.choose_features()
        print(user_feats)
        if len(user_feats) == 0:
            self.feats = list(([], [], []))
        else:
            self.feats = map_requested_features_to_defined_features(user_feats)

        assert isinstance(self.feats, list), "feats is a list"
        assert len(self.feats) == 3
        print(self.feats)

        print("\n 1a.1")
        print("Sending Features code")
        msg = QtCore.QByteArray()
        msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
        msg_stream.writeInt64(message_ids["MSG_ID_feats_code"])
        # feats must be sent one by one, list of lists doesn't work
        print("Sending Features")
        for feat in self.feats:
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

        print("Receiving Parameters...")
        rcv = QtCore.QByteArray(self.socket_rr.recv())
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        self.reg_features.scalars = rcv_stream.readQStringList()
        self.reg_features.traces = rcv_stream.readQStringList()
        self.reg_features.images = rcv_stream.readQStringList()
        self.image_shape = qstream_read_array(rcv_stream, np.uint16)
        # image_shape_len = 2
        self.scalar_len = len(self.reg_features.scalars)
        self.vector_len = len(self.reg_features.traces)
        self.image_len = len(self.reg_features.images)
        # print(image_shape_len)
        # print(image_shape)
        # assert image_shape_len == len(image_shape)

        print(" Registered data container formats:")
        print(" scalars:", self.reg_features.scalars)
        print(" traces:", self.reg_features.traces)
        print(" images:", self.reg_features.images)
        print(" image_shape:", self.image_shape)

    def request_data_transfer(self):
        # make sure to start the subscriber before the publisher to
        # not miss data transfer
        # start separate thread for data transfer
        self.start_subscriber_thread()

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

    def start_subscriber_thread(self):
        print("\n 2a.")
        print("Starting Subscriber Thread")
        sub_thread = Thread(target=subscriber_thread,
                            args=(self,))
        sub_thread.daemon = True
        sub_thread.start()
        # subscriber_thread(self)

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
            print("Client closing")
        else:
            raise ValueError("ID code not correct, should be "
                             f"{message_ids['MSG_ID_end_reply']}")

    def run_event_message(self, rcv_stream):
        e = EventData()
        r = rcv_stream.readInt64()
        e.id = r

        if self.scalar_len > 0:
            e.scalars = qstream_read_array(rcv_stream, np.float64)
            assert len(e.scalars) == self.scalar_len

        if self.vector_len > 0:
            n_traces = rcv_stream.readUInt32()
            assert n_traces == self.vector_len
            # read traces piece by piece
            for i in range(n_traces):
                e.traces.append(qstream_read_array(rcv_stream, np.int16))

        if self.image_len > 0:
            n_images = rcv_stream.readUInt32()
            assert n_images == self.image_len
            # read images piece by piece, checking for binary mask
            for im_name in self.reg_features.images:
                if im_name == "mask":
                    mask_data = qstream_read_array(rcv_stream, np.bool_)
                    e.images.append(mask_data.reshape(self.image_shape))
                elif im_name == "contour":
                    contour_data = qstream_read_array(rcv_stream, np.uint8)
                    e.images.append(
                        contour_data.reshape(len(contour_data) // 2, 2))
                elif im_name == "image":
                    image_data = qstream_read_array(rcv_stream, np.uint8)
                    e.images.append(image_data.reshape(self.image_shape))
                else:
                    raise ValueError(
                        "Image feature '{}' not recognised".format(im_name))
        return e

    def after_register(self):
        """Called after registration with Shape-In is complete"""
        pass

    def after_transmission(self):
        """Called after Shape-In ends data transmission"""

    @abc.abstractmethod
    def handle_event(self, event_data: EventData) -> bool:
        """Abstract method to be overridden by plugins implementations"""
        return False

    @abc.abstractmethod
    def choose_features(self):
        """Abstract method to be overridden by plugins implementations.

        Notes
        -----
        When features are chosen by a plugin implementation, only those chosen
        features will be transferred between ShapeIn and the plugin. This has
        the effect of ignoring any features specified by the user in the
        --features (-f) option of the command line interface.

        """
        return list()


# def run_client():
#     cl = ShapeLinkPlugin()
#     cl.run_client()
