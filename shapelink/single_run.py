
import threading

from shapelink import server_simulator
from shapelink import client_plugin


th = threading.Thread(target=client_plugin.run_client)
th.start()

server_simulator.start_simulator()
