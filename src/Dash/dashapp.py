from dash import Dash, Input

from .base import layout


def create_dashapp(server, base_url):
    """
    Init our dashapp, to be embedded into flask
    """

    app = Dash(
        __name__,
        server=server,
        url_base_pathname=base_url,
        use_pages=True,
        pages_folder="pages",
        prevent_initial_callbacks="initial_duplicate",
        suppress_callback_exceptions=True,
        routing_callback_inputs={"socket_ids": Input("dash_websocket", "socketId")},
    )
    # Set favicon
    # app._favicon = f"{assets_path}/img/favicon.ico"
    app.title = "Stock"

    app.layout = layout

    return app.server
