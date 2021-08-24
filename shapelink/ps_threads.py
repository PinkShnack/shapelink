
import zmq
import time
import numpy as np
import dclab
from typing import List
from PySide2 import QtCore

from .util import qstream_write_array
from .msg_def import topicfilter_ids


def subscriber_thread(client_object):
    client_object.socket_ps.setsockopt(zmq.SUBSCRIBE,
                                       topicfilter_ids["topicfilter_001"])

    while True:
        [_, data] = client_object.socket_ps.recv_multipart()
        rcv = QtCore.QByteArray(data)
        rcv_stream = QtCore.QDataStream(rcv, QtCore.QIODevice.ReadOnly)
        e = client_object.run_event_message(rcv_stream)
        client_object.handle_event(e)


def publisher_thread(server_object):
    send_dataset(server_object)


def send_dataset(server_object):
    """The job of this function is to simulate the shapein sending transfer
    It just sends the events as they come"""
    sc_features, tr_features, im_features = server_object.feats
    with dclab.new_dataset(server_object.simulator_path) as ds:
        if server_object.verbose:
            print("Opened dataset", ds.identifier, ds.title)

        t0 = time.perf_counter_ns()
        c = 0

        if server_object.verbose:
            print("Send event data:")
        for event_index in range(len(ds)):
            scalars = list()
            vectors = list()
            images = list()

            for feat in sc_features:
                scalars.append(ds[feat][event_index])
            for feat in tr_features:
                tr = np.array(ds['trace'][feat][event_index], dtype=np.int16)
                vectors.append(tr)
            for feat in im_features:
                if ds[feat][event_index].dtype == bool:
                    im = np.array(ds[feat][event_index], dtype=bool)
                else:
                    im = np.array(ds[feat][event_index], dtype=np.uint8)
                images.append(im)

            send_event(server_object,
                       event_index,
                       np.array(scalars, dtype=np.float64),
                       vectors,
                       images)
            c += 1

        if server_object.verbose:
            t1 = time.perf_counter_ns()
            dt = (t1 - t0) * 1e-9
            time.sleep(0.2)
            print("Simulation event rate: {:.5g} Hz".format(c / dt))
            print("Simulation time per event: {:.5g} s".format(dt / c))
            print("Simulation time: {:.5g} s".format(dt))
            print("Publisher Finished Data Transfer")


def send_event(server_object,
               event_id: int,
               scalar_values: np.array,
               # vector of vector of short
               vector_values: List[np.array],
               image_values: List[np.array]):
    """Send a single event to the other process"""

    # prepare message in byte stream
    msg = QtCore.QByteArray()
    msg_stream = QtCore.QDataStream(msg, QtCore.QIODevice.WriteOnly)
    msg_stream.writeInt64(event_id)

    assert len(scalar_values) == server_object.scalar_len
    assert len(vector_values) == server_object.vector_len
    assert len(image_values) == server_object.image_len
    assert np.issubdtype(scalar_values.dtype, np.floating)

    if server_object.scalar_len > 0:
        qstream_write_array(msg_stream, scalar_values)

    if server_object.vector_len > 0:
        msg_stream.writeUInt32(server_object.vector_len)
        for e in vector_values:
            assert e.dtype == np.int16, "fluorescence data is int16"
            qstream_write_array(msg_stream, e)

    if server_object.image_len > 0:
        msg_stream.writeUInt32(server_object.image_len)
        for (im_name, e) in zip(server_object.image_names, image_values):
            if im_name == "mask":
                assert e.dtype == np.bool_, "'mask' data is bool"
            else:
                assert e.dtype == np.uint8, "'image' data is uint8"
            qstream_write_array(msg_stream, e.flatten())

    try:
        # send the message over the socket
        # multippart message with topicfilter as first part
        # parse that info on subscriber side and run handle_event with it.
        server_object.socket_ps.send_multipart(
            [topicfilter_ids["topicfilter_001"], msg])
    except zmq.error.ZMQError:
        print("ZMQ Error")
