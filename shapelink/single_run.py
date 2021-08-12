
import threading

from shapelink import server_simulator
from shapelink import client_plugin


# might have to start client in this thread.
th = threading.Thread(target=server_simulator.start_simulator)
th.start()

client_plugin.run_client()
