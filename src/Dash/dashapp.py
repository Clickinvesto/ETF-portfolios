from dash import Dash, Input, _dash_renderer
from flask import current_app
from .base import layout

_dash_renderer._set_react_version("18.2.0")
import diskcache
from dash.long_callback import DiskcacheLongCallbackManager

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

stylesheets = [
    "https://unpkg.com/@mantine/dates@7/styles.css",
    # "https://unpkg.com/@mantine/code-highlight@7/styles.css",
    # "https://unpkg.com/@mantine/charts@7/styles.css",
    # "https://unpkg.com/@mantine/carousel@7/styles.css",
    "https://unpkg.com/@mantine/notifications@7/styles.css",
    # "https://unpkg.com/@mantine/nprogress@7/styles.css",
]


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
        external_stylesheets=stylesheets,
        prevent_initial_callbacks="initial_duplicate",
        suppress_callback_exceptions=True,
        routing_callback_inputs={"socket_ids": Input("dash_websocket", "socketId")},
        assets_folder="../assets",
        long_callback_manager=long_callback_manager,
    )
    # Set favicon
    # app._favicon = f"{assets_path}/img/favicon.ico"
    app.title = "Stock"

    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID"></script>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """
    app.index_string = app.index_string.replace(
        "YOUR_CLIENT_ID", current_app.config["PAYPAL_CLIENT_ID"]
    )

    app.layout = layout

    return app.server
