import importlib
import pathlib
import sys
import threading

import click

from . import shapein_simulator
from . import server_simulator
from . import client_plugin


@click.group()
def main():
    pass


features_help_text = (
        "Comma-separated list of features to send by the "
        + "Shape-In simulator; Defaults to all innate features. "
        + "A list of valid feature names can be found in "
        + "the dclab docs (Advanced Usage -> Notation). "
        + "The list of features will be ignored if any features "
        + "are specified within the `choose_features` method of a "
        + "plugin implementation.")


@click.command()
@click.argument("path")
@click.option("--features", "-f",
              help=features_help_text)
def run_simulator(path, features=None):
    """Run the Shape-In simulator using data from an RT-DC dataset file

    Example usage::

       shape-link run-simulator --features image,deform /path/to/data.rtdc
    """
    if features is not None:
        features = [f.strip() for f in features.split(",")]
    shapein_simulator.start_simulator(path, features)


@click.command()
@click.option("--with-simulator", "-w",
              help="Run the Shape-In simulator in the background "
                   + "using the RT-DC dataset specified (used for testing).")
def run_plugin(with_simulator=None):
    """Run a Shape-Link plugin file

    Example usages::

        # run a plugin
        shape-link run-plugin plugins/slp_rolling_mean.py
        # run a plugin with a simulator thread (for plugin testing)
        shape-link run-plugin -w data.rtdc -f image,deform slp_rolling_mean.py


    """

    # path = pathlib.Path(path)
    # # insert the plugin directory to sys.path so we can import it
    # sys.path.insert(-1, str(path.parent))
    # plugin = importlib.import_module(path.stem)
    # # undo our path insertion
    # sys.path.pop(0)
    # # run the plugin
    # click.secho("Running Shape-Link plugin '{}'...".format(path.stem),
    #             bold=True)
    # p = plugin.info["class"]()
    # while True:
    #     p.handle_messages()

    th = threading.Thread(target=client_plugin.run_client)
    th.start()
    # just handle path with the start_simulator function
    if with_simulator is not None:
        server_simulator.start_simulator(with_simulator)
    else:
        raise ValueError("We haven't implemented actual transfer yet.")


main.add_command(run_simulator)
main.add_command(run_plugin)
