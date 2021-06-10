import shutil
import pathlib
import dclab
from dclab.features.emodulus import get_emodulus

from shapelink import ShapeLinkPlugin

# We use the terminal width to make sure a line doesn't get cluttered
# with prints from a previous line.
TERMINAL_WIDTH = shutil.get_terminal_size((80, 20))[0]

data_dir = pathlib.Path(__file__).parent / "../tests/data"
ds_test = dclab.new_dataset(data_dir / "calibration_beads_47.rtdc")


class RTDCSortingComputeFeatureShapeLinkPlugin(ShapeLinkPlugin):
    """Check if the aspect ratio is correctly calculated.
    Shows a user how to choose features"""
    def __init__(self, *args, **kwargs):
        super(RTDCSortingComputeFeatureShapeLinkPlugin, self).__init__(*args, **kwargs)

    def after_register(self):
        print(" Preparing for transmission")

    def after_transmission(self):
        print("\n End of transmission\n")

    def choose_features(self):
        user_feats = ['area_ratio', 'area_um', 'bright_avg', 'deform']
        return user_feats

    def handle_event(self, event_data):
        """Filter the feature information an trigger pulse

        - Compute the emodulus from transferred features
        - Set the desired gates/filters for each filter
        - Send a trigger to the surface acoustic wave software if the
        object needs to be sorted into the target
        """
        assert self.reg_features.scalars == [
            'area_ratio', 'area_um', 'bright_avg', 'deform']

        area_ratio, area_um, bright_avg, deform = event_data.scalars
        print(area_ratio, area_um, bright_avg, deform)

        calccfg = ds_test.config["calculation"]
        # lut_identifier = calccfg["emodulus model"]
        lut_identifier = "LE-2D-FEM-19"

        # whether to sent a trigger to the surface wave software
        trigger = False
        # example gates/filters
        rules = [1.0 < area_ratio < 1.2,
                 5 < area_um < 200,
                 31 < bright_avg < 35,
                 0.0 < deform < 0.27]
        if all(rules):
            # only compute emod if all other gates are passed
            # compute emodulus
            emod = get_emodulus(
                area_um=area_um, deform=deform,
                medium="CellCarrier", channel_width=20.0,
                flow_rate=0.16, px_um=0.34, temperature=23.0,
                lut_data=lut_identifier)
            if 5 < emod < 10:
                trigger = True

            print(emod)

        # example logging output
        print(str(trigger))

        return False


info = {
    "class": RTDCSortingComputeFeatureShapeLinkPlugin,
    "description": "Gates the feature info and send trigger to "
                   "surface acoustic wave software",
    "name": "RTDC Sorting",
    "version": "0.1.0",
}
