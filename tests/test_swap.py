import pathlib
import threading

from shapelink.client_plugin import ShapeLinkPlugin, EventData
from shapelink.server_simulator import start_simulator


data_dir = pathlib.Path(__file__).parent / "data"


class ExampleShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = ["size_x", "size_y", "aspect"]
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        print("Event handled")

        return False


def test_run_plugin_with_simulator():
    verbose = False
    p = ExampleShapeLinkPlugin(verbose=verbose)
    th = threading.Thread(target=p.run_client)
    th.start()

    start_simulator(str(data_dir / "calibration_beads_47.rtdc"),
                    verbose=verbose)


def test_run_plugin_with_simulator_verbose():
    verbose = True
    p = ExampleShapeLinkPlugin(verbose=verbose)
    th = threading.Thread(target=p.run_client)
    th.start()

    start_simulator(str(data_dir / "calibration_beads_47.rtdc"),
                    verbose=verbose)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
