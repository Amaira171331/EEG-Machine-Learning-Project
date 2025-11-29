from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import threading

# Handlers
def alpha_handler(address, *args):
    print("Alpha:", args)  # Muse alpha_absolute data

def beta_handler(address, *args):
    print("Beta:", args)   # Muse beta_absolute data

# Dispatcher
disp = Dispatcher()
disp.map("/muse/elements/alpha_absolute", alpha_handler)
disp.map("/muse/elements/beta_absolute", beta_handler)

# OSC Server
server = BlockingOSCUDPServer(("0.0.0.0", 9001), disp)
print("Python OSC listening on 0.0.0.0:9001")

# Run server in a background thread
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

# Keep Python alive
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting")
    server.shutdown()
    server.server_close()
