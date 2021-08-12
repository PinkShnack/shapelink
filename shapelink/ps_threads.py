
import zmq
import time
import random
import numpy as np
import dclab
from typing import List
from PySide2 import QtCore

from shapelink.util import qstream_write_array


topicfilter = b'A'


def subscriber_thread(client_object):
    # start separate thread

    client_object.socket_ps.setsockopt(zmq.SUBSCRIBE, topicfilter)

    while True:
        # data = client_object.socket_ps.recv_string()
        # run the plugin run_event_message then handle_event
        # which will execute your custom plugin
        # topic, messagedata = data.split()
        # print(messagedata)
        [topic, data] = client_object.socket_ps.recv_multipart()
        client_object.handle_event(data)


def publisher_thread(server_object):

    # while True:
    #     code = "A"
    #     event_id = random.randint(1, 10)
    #     messagedata = f"data_{event_id}"
    #     server_object.socket_ps.send_string(f"{code}, {messagedata}")
    #     time.sleep(0.5)

    send_event_data(server_object)


# The job of this function is to simulate the shapein sending transfer
# It just sends the events as they come
def send_event_data(server_object):
    sc_features, tr_features, im_features = server_object.feats
    with dclab.new_dataset(server_object.simulator_path) as ds:
        if server_object.verbose:
            print("Opened dataset", ds.identifier, ds.title)

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
            print(f"Sending event {event_index}")
            time.sleep(0.2)

    print("Finished Data Transfer from pub side")


# multippart message with topicfilter as first part
# parse that info on subscriber side and run handle_event with it.
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
        server_object.socket_ps.send_multipart([topicfilter, msg])
    except zmq.error.ZMQError:
        print("ZMQ Error")
