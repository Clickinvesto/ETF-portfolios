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

    def add_RI(self, data, configuration):
        hover_text = [
            f"Age (month): {age}"
            for age in data.filter(pl.col("Series") == "RI")
            .select("Age")
            .to_series()
            .to_list()
        ]
        self.figure.add_trace(
            go.Scatter(
                x=data.filter(pl.col("Series") == "RI")
                .select(configuration.get("x_value", "Risk"))
                .to_series()
                .to_list(),
                y=data.filter(pl.col("Series") == "RI")
                .select(configuration.get("y_value", "CAGR"))
                .to_series()
                .to_list(),
                mode="markers",
                customdata=data.filter(pl.col("Series") == "RI")
                .select("Series")
                .to_series()
                .to_list(),
                marker_color=data.filter(pl.col("Series") == "RI")
                .select("color")
                .to_series()
                .to_list(),
                name="RI",
                marker=dict(color="#add8e6", size=8),
                text=hover_text,
                hovertemplate="Series: %{customdata}<br>CAGR: %{y:.2f}%<br>Risk: %{x:.2f}%<br>%{text}<extra></extra>",
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
            title_y=0.92,
            autosize=False,
            title_xanchor="center",
            title_yanchor="top",
            title_font=dict(size=config.get("title_font_size", 20)),
            font=dict(size=config.get("generel_font_size", 16)),
        )
        fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01))

        self.figure = fig

    def prepare_age(self, data):
        color_dict = {"young": "#a8d4ff", "middle": "#0b88ff", "old": "#002446"}

        # Calculate Age Categories
        age_values = (
            data.filter(pl.col("Series") != "RI").select("Age").to_series().to_list()
        )
        min_age = min(age_values)
        max_age = max(age_values)
        range_age = max_age - min_age
        section_length = range_age / 3

        data = data.with_columns(
            pl.when(pl.col("Age") <= min_age + section_length)
            .then(pl.lit("young"))
            .when(pl.col("Age") <= min_age + 2 * section_length)
            .then(pl.lit("middle"))
            .otherwise(pl.lit("old"))
            .alias("categorised_age")
        )
        data = data.with_columns(
            pl.when(pl.col("categorised_age") == "young")
            .then(pl.lit(color_dict["young"]))
            .when(pl.col("categorised_age") == "middle")
            .then(pl.lit(color_dict["middle"]))
            .otherwise(pl.lit(color_dict["old"]))
            .alias("color")
        )
        return data

    def make_dispersion_plot(self, data, dropdown_value=None):
        self.update_config()
        configuration = self.cofiguration.get("dispersion")
        self.init_graph(configuration)
        self.figure.update_layout(
            title_text=configuration.get("title", "Dispersion Graph")
        )

        self.figure.update_layout(clickmode="event+select")

        data = self.prepare_age(data)

        hover_text = [
            f"Age (month): {age}"
            for age in data.filter(pl.col("Series") != "RI")
            .select("Age")
            .to_series()
            .to_list()
        ]

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
                customdata=data.filter(pl.col("Series") != "RI")
                .select("Series")
                .to_series()
                .to_list(),
                marker_color=data.filter(pl.col("Series") != "RI")
                .select("color")
                .to_series()
                .to_list(),
                text=hover_text,
                hovertemplate="Series: %{customdata}<br>CAGR: %{y:.2f}%<br>Risk: %{x:.2f}%<br>%{text}<extra></extra>",
                selected={
                    "marker": {
                        "color": self.get_color(configuration.get("selected_color"))
                    }
                },
            )
        )

        self.figure.update_yaxes(
            ticksuffix=" %", anchor="free", title=configuration.get("y_value", "CAGR")
        )
        self.figure.update_xaxes(
            ticksuffix=" %", title=configuration.get("x_value", "Risk")
        )
        self.add_RI(data, configuration)

        # Add dropdown
        self.figure.update_layout(
            updatemenus=[
                dict(
                    buttons=list(
                        [
                            dict(
                                args=["store", "All Portfolios"],
                                label="All Portfolios",
                                method="relayout",
                            ),
                            dict(
                                args=["store", "Better than RI"],
                                label="Better than RI",
                                method="relayout",
                            ),
                        ]
                    ),
                    direction="down",
                    pad={"l": -50, "t": -10},
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=1.1,
                    yanchor="top",
                    font=dict(size=13),
                    active=(
                        0
                        if dropdown_value is None
                        else (0 if dropdown_value == "All Portfolios" else 1)
                    ),
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

            data.index = data.index.strftime("%Y-%m-%d")
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

            self.figure.update_layout(
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
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
