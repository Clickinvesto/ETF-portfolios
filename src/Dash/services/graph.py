import json
import polars as pl
from pathlib import Path
import plotly.graph_objects as go
from flask import current_app
import plotly.express as px

color_set = px.colors.qualitative.Vivid


def blank_fig():
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


class plotting_engine:
    def __init__(self) -> None:
        self.working_directory = Path.cwd()
        self.config_folder = "src/Dash/config"
        self.graph_file = "graphs.json"
        self.graph_path = Path.joinpath(
            self.working_directory, self.config_folder, self.graph_file
        )

    def add_RI(self, y, x):
        self.figure.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                name="RI",
                marker=dict(color="#add8e6", size=8),
                mode="markers",
                hovertemplate="CAGR: %{y:.2f}%<br>Risk: %{x:.2f}%<extra></extra>",
            )
        )

    def get_color(self, color):
        if isinstance(color, str):
            return color
        return color_set[color]

    def update_config(self):
        f = open(self.graph_path)
        data = json.load(f)
        self.cofiguration = data

    def init_graph(self, config):

        fig = go.Figure()
        fig.update_layout(
            yaxis=dict(showline=True, showgrid=True),
            xaxis=dict(showline=True, showgrid=True),
        )
        fig.update_xaxes(rangeslider_visible=False)
        fig.update_layout(
            title_x=0.5,
            autosize=True,
            title_xanchor="center",
            title_yanchor="top",
            title_font=dict(size=config.get("title_font_size", 20)),
            font=dict(size=config.get("generel_font_size", 16)),
        )

        self.figure = fig

    def make_dispersion_plot(self, data, dropdown_value=None):
        self.update_config()
        configuration = self.cofiguration.get("dispersion")
        self.init_graph(configuration)
        self.figure.update_layout(
            title_text=configuration.get("title", "Dispersion Graph")
        )

        self.figure.update_layout(clickmode="event+select")
        self.figure.add_trace(
            go.Scatter(
                x=data.filter(pl.col("Series") != "RI")
                .select(configuration.get("x_value", "Risk"))
                .to_series()
                .to_list(),
                y=data.filter(pl.col("Series") != "RI")
                .select(configuration.get("y_value", "CAGR"))
                .to_series()
                .to_list(),
                mode="markers",
                name="Portfolios",
                text=data.filter(pl.col("Series") != "RI")
                .select("Series")
                .to_series()
                .to_list(),
                hovertemplate="CAGR: %{y:.2f}%<br>Risk: %{x:.2f}%<extra></extra>",
                marker=dict(color=self.get_color(configuration.get("color_marker", 5))),
                selected={
                    "marker": {
                        "color": self.get_color(configuration.get("selected_color"))
                    }
                },
            )
        )
        self.figure.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1)
        )

        self.figure.update_yaxes(
            ticksuffix=" %", anchor="free", title=configuration.get("y_value", "CAGR")
        )
        self.figure.update_xaxes(
            ticksuffix=" %", title=configuration.get("x_value", "Risk")
        )

        ref_series = configuration.get("reference_series")
        ri_cagr = data.filter(pl.col("Series") == "RI").select(configuration.get("y_value", "CAGR")).item(0, 0)
        ri_risk = data.filter(pl.col("Series") == "RI").select(configuration.get("x_value", "Risk")).item(0, 0)
        self.add_RI(ri_cagr, ri_risk)

        # Add dropdown
        self.figure.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=["store", "All Portfolios"],
                            label="All Portfolios",
                            method="relayout"
                        ),
                        dict(
                            args=["store", "Better than RI"],
                            label="Better than RI",
                            method="relayout"
                        )
                    ]),
                    direction="down",
                    pad={"l": -50, "t": -10},
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=1.1,
                    yanchor="top",
                    font=dict(size=13),
                    active=0 if dropdown_value is None else (0 if dropdown_value == "All Portfolios" else 1),
                ),
            ]
        )
        return self.figure

    def make_performance_plot(self, data, series):
        try:
            self.update_config()
            configuration = self.cofiguration.get("performance")
            reference_series = configuration.get("reference_series", "RI")

            link = current_app.config["URL_COMPOSITION"] + f"?series={series}"

            self.init_graph(configuration)
            title = f"{configuration.get('title', 'Performance Graph')} of {series}"
            self.figure.update_layout(title_text=title)

            self.figure.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1, xanchor="right", x=1
                )
            )
            self.figure.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[series].tolist(),
                    mode="lines",
                    name=series,
                    line=dict(width=2.5),
                    marker=dict(
                        color=self.get_color(
                            configuration.get("selected_series_color", "blue")
                        ),
                    ),
                )
            )
            self.figure.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[reference_series].tolist(),
                    mode="lines",
                    name=configuration.get("reference_series_name", "SAP"),
                    marker=dict(
                        color=self.get_color(
                            configuration.get("reference_color", "blue")
                        )
                    ),
                )
            )
            self.figure.update_xaxes(
                tickformat=configuration.get("date_format", "%d/%m/%Y"), tickangle=-45
            )

            return self.figure

        except Exception as e:
            return "error", e

    def make_pie_chart(self, labels, values, series):
        self.update_config()
        configuration = self.cofiguration.get("composition")

        self.init_graph(configuration)
        title = f"{configuration.get('title', 'Composition')} of {series}"
        self.figure.update_layout(title_text=title)
        self.figure.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=[
                    "#004c94",
                    " #255e9f",
                    "#3e6fab",
                    "#5681b6",
                    "#6d93c1",
                    "#85a4cb," "#9db6d6",
                    "#b5c8e1",
                    "#cddaeb",
                    "#e6edf5",
                ],
                hoverinfo="skip",
            )
        )

        return self.figure
