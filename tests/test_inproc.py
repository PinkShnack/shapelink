import pathlib
import threading

from shapelink import shapein_simulator
from shapelink import ShapeLinkPlugin
from shapelink.shapelink_plugin import EventData

data_dir = pathlib.Path(__file__).parent / "data"


class ChooseFeaturesShapeLinkPlugin(ShapeLinkPlugin):
    """Simple plugin that checks if the correct features are transferred"""
    def __init__(self, *args, **kwargs):
        super(ChooseFeaturesShapeLinkPlugin, self).__init__(*args, **kwargs)

    def choose_features(self):
        return ["time", "image"]

    def handle_event(self, event_data: EventData) -> bool:
        """Check that the chosen features were transferred"""
        assert self.reg_features.scalars == ["time"]
        assert self.reg_features.images == ["image"]
        return False


def test_run_plugin_with_user_defined_features():
    """Server and Client connected via inproc"""
    # create new thread for simulator
    th = threading.Thread(target=shapein_simulator.start_simulator,
                          args=(str(data_dir / "calibration_beads_47.rtdc"),
                                None, "inproc://t", 0)
                          )
    # setup plugin
    p = ChooseFeaturesShapeLinkPlugin(bind_to='inproc://t')
    # start simulator
    th.start()
    # start plugin
    for ii in range(49):
        p.handle_messages()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
