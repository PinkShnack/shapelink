
from shapelink import ShapeLinkPlugin


class RTDCSortingBasicShapeLinkPlugin(ShapeLinkPlugin):
    """Simulate the gates used for sorting rtdc data live"""
    def __init__(self, *args, **kwargs):
        super(RTDCSortingBasicShapeLinkPlugin, self).__init__(*args, **kwargs)

    def after_register(self):
        print(" Preparing for transmission")

    def after_transmission(self):
        print("\n End of transmission\n")

    def choose_features(self):
        user_feats = ['area_ratio', 'area_um', 'bright_avg', 'deform']
        return user_feats

    def handle_event(self, event_data):
        """Gate the feature information and display sorted events

        - Set the desired gates/filters for each filter
        - Compute the emodulus from transferred features
        - Send a trigger to the surface acoustic wave software if the
          object needs to be sorted into the target
        """
        assert self.reg_features.scalars == [
            'area_ratio', 'area_um', 'bright_avg', 'deform']

        area_ratio, area_um, bright_avg, deform = event_data.scalars

        # used to sent a trigger to the surface acoustic wave software
        trigger = False
        # example gates/filters
        rules = [1.0 < area_ratio < 1.2,
                 5 < area_um < 200,
                 31 < bright_avg < 35,
                 0.0 < deform < 0.27]
        if all(rules):
            trigger = True

        # example logging output
        print(str(trigger))

        return False


info = {
    "class": RTDCSortingBasicShapeLinkPlugin,
    "description": "Gates the feature info and send trigger to "
                   "surface acoustic wave (SAW) software",
    "name": "RTDC Sorting Basic",
    "version": "0.1.0",
}
