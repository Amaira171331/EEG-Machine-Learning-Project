import threading
from datetime import datetime
import os 
import sys # Import sys for better error handling

import eventlet
import socketio
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

# --- File Configuration ---
CLIENT_FILENAME = 'EEG_Adaptive_Interface_HTMLVERSION.html' # CORRECTED FILE NAME!
# --------------------------


# --- Socket.IO Server Setup ---

# Initialize Socket.IO server with cross-origin allowed for the web client
sio = socketio.Server(cors_allowed_origins="*")

# Resolve the absolute path of the client file
dir_path = os.path.dirname(os.path.realpath(__file__))
static_file_path = os.path.join(dir_path, CLIENT_FILENAME)

# Print the path the server is trying to access for verification
print(f"Serving client file from: {static_file_path}")

app = socketio.WSGIApp(
    sio,
    static_files={
        "/": {"content_type": "text/html", "filename": static_file_path}
    },
)

# --- Socket.IO Event Emitters ---
def send_alpha_absolute(value):
    sio.emit("alpha_absolute", value)

def send_alpha_relative(value):
    sio.emit("alpha_relative", value)

def send_beta_absolute(value):
    sio.emit("beta_absolute", value)

def send_beta_relative(value):
    sio.emit("beta_relative", value)


@sio.event
def connect(sid, environ):
    """Handles new client connections."""
    print(f"Client connected: {sid} at {datetime.now().strftime('%H:%M:%S')}")


@sio.event
def disconnect(sid):
    """Handles client disconnections."""
    print(f"Client disconnected: {sid} at {datetime.now().strftime('%H:%M:%S')}")


# --- OSC Handlers (MODIFIED FOR ROBUSTNESS) ---

def generic_handler(address, handler_func, *args):
    """
    A generic handler to parse OSC arguments and call the appropriate Socket.IO sender.
    This is updated to be robust against single-item lists/tuples often sent by TouchDesigner.
    """
    if not args:
        print(f"Warning: Received OSC message on {address} with no arguments.")
        return

    # Attempt to extract the first argument, handling cases where it might be wrapped.
    try:
        # If the first item is iterable (like a list/tuple) and has items, use the first item in it.
        # This handles the common TouchDesigner case where a single value is sent as a tuple.
        if isinstance(args[0], (list, tuple)) and args[0]:
            value_candidate = args[0][0]
        else:
            value_candidate = args[0]
            
        value = float(value_candidate)
        
        # Confirmation print for debugging
        print(f"Received: {address}, Value: {value:.4f}") 
        
        handler_func(value)
        
    except ValueError:
        # Catch errors if the argument cannot be converted to a float
        print(f"Error: Could not convert OSC value '{value_candidate}' to float for {address}.", file=sys.stderr)
    except Exception as e:
        # Catch any other unexpected error
        print(f"Unexpected error processing OSC message on {address}: {e}", file=sys.stderr)


def alpha_absolute_osc_handler(address, *args):
    # Only map the required addresses
    if address == "/muse/elements/alpha_absolute":
        generic_handler(address, send_alpha_absolute, *args)

def alpha_relative_osc_handler(address, *args):
    # Only map the required addresses
    if address == "/muse/elements/alpha_relative":
        generic_handler(address, send_alpha_relative, *args)

def beta_absolute_osc_handler(address, *args):
    # Only map the required addresses
    if address == "/muse/elements/beta_absolute":
        generic_handler(address, send_beta_absolute, *args)

def beta_relative_osc_handler(address, *args):
    # Only map the required addresses
    if address == "/muse/elements/beta_relative":
        generic_handler(address, send_beta_relative, *args)


# --- OSC Dispatcher and Server Setup ---

dispatcher = Dispatcher()
# Map the specific addresses we want to receive
dispatcher.map("/muse/elements/alpha_absolute", alpha_absolute_osc_handler)
dispatcher.map("/muse/elements/alpha_relative", alpha_relative_osc_handler)
dispatcher.map("/muse/elements/beta_absolute", beta_absolute_osc_handler)
dispatcher.map("/muse/elements/beta_relative", beta_relative_osc_handler)

# OSC server listens on UDP port 9001 on all interfaces
osc_server = BlockingOSCUDPServer(("0.0.0.0", 9001), dispatcher)


def run_osc():
    """Function to run the OSC server in its own thread."""
    print("OSC server listening on port 9001 (UDP)...")
    try:
        osc_server.serve_forever()
    except Exception as e:
        print(f"OSC Server Error: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    # Start the OSC server in a background thread
    threading.Thread(target=run_osc, daemon=True).start()

    print("WebSocket (Socket.IO) server running on port 5670(HTTP)...")
    # Start the Socket.IO web server
    eventlet.wsgi.server(eventlet.listen(("", 5670)), app)