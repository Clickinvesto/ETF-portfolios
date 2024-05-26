import eventlet

eventlet.monkey_patch(socket=False, select=False, time=False, os=False)

import sys


# Patch openpay.util.utf8 function
def utf8(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return value


# Apply the patch
import openpay.util

openpay.util.utf8 = utf8

from src import create_app
from flask_socketio import SocketIO
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Here we start our application server

app = create_app()
# socketio = SocketIO(app, async_mode="gevent")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
if __name__ == "__main__":
    socketio.run(app, debug=True)
    # socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
    # socketio.run(app, port=int(os.getenv("DASHBOARD_PORT", 8051)))
