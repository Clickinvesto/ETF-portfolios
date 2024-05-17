import dash_mantine_components as dmc
import json
from dash import html
from dash_iconify import DashIconify
from flask import current_app
from flask_socketio import SocketIO, emit, join_room
from plotly.io.json import to_json_plotly


def jsonify_data(data):
    return json.loads(to_json_plotly(data))


class NotificationProvider:
    """
    This calss provides you the ability to sent notifications.
    1. Initialise it at the top e.g. notify = NotificationProvider().
    2. In your callback include State(GeneralIDs.socket("base"), "socketId")
    3. Send notifications like:
            notification_id = uuid.uuid4().hex
            notify.send_socket(to=socket_id, type="start_process", id=notification_id)

    You can use preconfigured notifications:
    1. type="start_process"
    2. type="success_process"
    3. type="error_process"
    4. type="success"
    5. type="error"

    Process notification use the same id, to update the showing process notification with success or error
    """

    def make(self, type, title=False, message=False, id=None):
        if type == "success_process":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title if title else "Data loaded",
                message=message if message else "Thank you for waiting",
                color="green",
                action="update",
            )
        elif type == "start_process":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title if title else "Querying data from the database",
                message=message if message else "Please wait a moment",
                loading=True,
                color="orange",
                action="show",
                autoClose=False,
            )

        elif type == "error_process":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title if title else "Error occured",
                message=(
                    message
                    if message
                    else "Please refresh the page and try again. We also logged the error"
                ),
                color="red",
                action="update",
            )

        elif type == "success":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title,
                message=message,
                color="green",
                action="show",
                autoClose=3 * 1000,
            )
        elif type == "error":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title,
                message=message,
                color="yellow",
                action="show",
                autoClose=3 * 1000,
            )
        elif type == "socket_success":
            return dmc.Notification(
                id="initialise_model" if id is None else id,
                title=title,
                message=message,
                loading=True,
                color="green",
                action="show",
                autoClose=False,
            )

    def send_socket(self, to, type, title=False, message=False, id=None):
        notification = self.make(type, title, message, id)
        emit(
            "notification",
            notification.to_plotly_json(),
            namespace="/",
            to=to,
        )
