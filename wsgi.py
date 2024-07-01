import eventlet

# eventlet.monkey_patch()

import sys
import os

# Add the project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from src import create_app
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Here we start our application server

app = create_app()

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
if __name__ == "__main__":
    socketio.run(app, debug=True)
