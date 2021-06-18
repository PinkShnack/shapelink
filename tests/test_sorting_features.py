
import pathlib
import numpy as np
import dclab
from dclab.features.emodulus import get_emodulus

from shapelink import ShapeLinkPlugin
from shapelink.shapelink_plugin import EventData

from .helper_methods import run_plugin_feature_transfer

data_dir = pathlib.Path(__file__).parent / "data"
ds_test = dclab.new_dataset(data_dir / "calibration_beads_47.rtdc")


class RTDCSortingCheckFeaturesShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = [
            'area_ratio', 'area_um', 'bright_avg', 'deform', 'index']
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        """Test for checking the relevant sorting feature data"""

        assert self.reg_features.scalars == [
            'area_ratio', 'area_um', 'bright_avg', 'deform', 'index']

        area_ratio, area_um, bright_avg, deform, index = event_data.scalars

        area_ratio_known = ds_test["area_ratio"]
        area_um_known = ds_test["area_um"]
        bright_avg_known = ds_test["bright_avg"]
        deform_avg_known = ds_test["deform"]

        index = int(index - 1)
        assert np.allclose(area_ratio, area_ratio_known[index])
        assert np.allclose(area_um, area_um_known[index])
        assert np.allclose(bright_avg, bright_avg_known[index])
        assert np.allclose(deform, deform_avg_known[index])

        return False


class RTDCSortingSendFeaturesShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = ['area_ratio', 'area_um', 'bright_avg', 'deform']
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        return False


class RTDCSortingGateFeatureShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = ['area_ratio', 'area_um', 'bright_avg', 'deform']
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        """Gate the feature information and display sorted events

        - Set the desired gates/filters for each filter
        - Send a trigger to the surface acoustic wave software if the
          object needs to be sorted into the target
        """
        area_ratio, area_um, bright_avg, deform = event_data.scalars
        # used to sent a trigger to the surface acoustic wave software
        trigger = False
        # example gates/filters
        rules = [5 < area_um < 200,
                 0.0 < deform < 0.27,
                 1.0 < area_ratio < 1.2,
                 31 < bright_avg < 35]
        if all(rules):
            trigger = True
        # example logging output
        print(str(trigger))

        return False


class RTDCSortingComputeEMODFeatureShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = ['area_um', 'deform', 'index']
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        """Compute the emodulus from transferred features"""

        area_um, deform, index = event_data.scalars
        # compute emodulus
        lut_identifier = "LE-2D-FEM-19"
        emod = get_emodulus(
            area_um=area_um, deform=deform,
            medium="CellCarrier B", channel_width=20.0,
            flow_rate=0.06, px_um=0.34, temperature=23.0,
            lut_data=lut_identifier)

        if not np.isnan(emod):
            index = int(index - 1)
            emod_known = ds_test["emodulus"][index]
            assert np.allclose(emod, emod_known)

        return False


class RTDCSortingGateEMODFeatureShapeLinkPlugin(ShapeLinkPlugin):
    def choose_features(self):
        user_feats = ['area_ratio', 'area_um', 'bright_avg', 'deform']
        return user_feats

    def handle_event(self, event_data: EventData) -> bool:
        """Filter the feature information an trigger pulse

        - Set the desired gates/filters for each filter
        - Compute the emodulus from transferred features
        - Send a trigger to the surface acoustic wave software if the
          object needs to be sorted into the target
        """
        area_ratio, area_um, bright_avg, deform = event_data.scalars
        # whether to sent a trigger to the surface acoustic wave software
        trigger = False
        # example gates/filters
        rules = [5 < area_um < 200,
                 0.0 < deform < 0.27,
                 1.0 < area_ratio < 1.2,
                 31 < bright_avg < 35]
        if all(rules):
            # only compute emod if all other gates are passed
            # compute emodulus
            lut_identifier = "LE-2D-FEM-19"
            emod = get_emodulus(
                area_um=area_um, deform=deform,
                medium="CellCarrier B", channel_width=20.0,
                flow_rate=0.06, px_um=0.34, temperature=23.0,
                lut_data=lut_identifier)
            if 5 < emod < 10:
                trigger = True
        # example logging output
        print(str(trigger))

        return False


def test_rtdc_sorting_check_features():
    """Check the sorting-related scalar information"""
    run_plugin_feature_transfer(RTDCSortingCheckFeaturesShapeLinkPlugin)


def test_rtdc_sorting_send_features():
    """Send the sorting-related scalar information"""
    run_plugin_feature_transfer(RTDCSortingSendFeaturesShapeLinkPlugin)


def test_rtdc_sorting_gate():
    """Check the sorting information against some gates"""
    run_plugin_feature_transfer(RTDCSortingGateFeatureShapeLinkPlugin)


def test_rtdc_sorting_compute_emod():
    """Compute emodulus"""
    run_plugin_feature_transfer(RTDCSortingComputeEMODFeatureShapeLinkPlugin)


def test_rtdc_sorting_gate_emod():
    """Check the sorting information against some gates (incl. emod)"""
    run_plugin_feature_transfer(RTDCSortingGateEMODFeatureShapeLinkPlugin)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
