import pathlib
import threading

from shapelink import shapein_simulator

data_dir = pathlib.Path(__file__).parent / "data"


def run_plugin_feature_transfer(shapelink_plugin, random_port=True):
    # setup plugin
    p = shapelink_plugin(random_port=random_port)
    port_address = p.port_address
    # create new thread for simulator
    th = threading.Thread(target=shapein_simulator.start_simulator,
                          args=(str(data_dir / "calibration_beads_47.rtdc"),
                                None,
                                "tcp://localhost:{}".format(port_address), 0)
                          )
    # start simulator
    th.start()
    # start plugin
    for ii in range(49):
        p.handle_messages()
