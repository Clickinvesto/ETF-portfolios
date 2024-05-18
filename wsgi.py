import eventlet

eventlet.monkey_patch()
from src import create_app
from flask_socketio import SocketIO
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Here we start our application server

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
if __name__ == "__main__":
    socketio = SocketIO(app)
    socketio.run(app, debug=True)
