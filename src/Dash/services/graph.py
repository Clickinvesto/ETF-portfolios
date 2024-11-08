import json
import polars as pl
from pathlib import Path
import plotly.graph_objects as go
from flask import current_app
import plotly.express as px

color_set = px.colors.qualitative.Vivid
cache = current_app.cache


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

        # Calculate the section limits and round to nearest integers
        lower_section = round(min_age + section_length)
        middle_section = round(min_age + 2 * section_length)
        upper_section = round(max_age)

        # Apply the categorization based on these rounded limits
        data = data.with_columns(
            pl.when(pl.col("Age") <= lower_section)
            .then(pl.lit(f"Younger than {lower_section}"))
            .when(pl.col("Age") <= middle_section)
            .then(pl.lit(f"Between {lower_section} and {middle_section}"))
            .otherwise(pl.lit(f"Older than {middle_section}"))
            .alias("categorised_age")
        )

        data = data.with_columns(
            pl.when(pl.col("categorised_age").str.contains("Younger"))
            .then(pl.lit(color_dict["young"]))
            .when(pl.col("categorised_age").str.contains("Between"))
            .then(pl.lit(color_dict["middle"]))
            .otherwise(pl.lit(color_dict["old"]))
            .alias("color")
        )
        age_categories = data.select("categorised_age").unique().to_series().to_list()
        return data, age_categories

    def make_dispersion_plot(self, data):
        self.update_config()
        configuration = self.cofiguration.get("dispersion")
        self.init_graph(configuration)
        self.figure.update_layout(
            title_text=configuration.get("title", "Dispersion Graph")
        )

        self.figure.update_layout(clickmode="event+select")

        data, age_categories = self.prepare_age(data)

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
        ri_cagr = data.filter(pl.col("Series") == "RI").select("CAGR").item(0, 0)
        filtered_data = data.filter(
            (pl.col("Series") != "RI") & (pl.col("CAGR") > ri_cagr)
        )
        self.figure.add_trace(
            go.Scatter(
                x=filtered_data.filter(pl.col("Series") != "RI")
                .select(configuration.get("x_value", "Risk"))
                .to_series()
                .to_list(),
                y=filtered_data.filter(pl.col("Series") != "RI")
                .select(configuration.get("y_value", "CAGR"))
                .to_series()
                .to_list(),
                mode="markers",
                name="Portfolios",
                customdata=filtered_data.filter(pl.col("Series") != "RI")
                .select("Series")
                .to_series()
                .to_list(),
                marker_color=filtered_data.filter(pl.col("Series") != "RI")
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
        self.add_RI(data, configuration)
        self.figure.update_yaxes(
            ticksuffix=" %", anchor="free", title=configuration.get("y_value", "CAGR")
        )
        self.figure.update_xaxes(
            ticksuffix=" %", title=configuration.get("x_value", "Risk")
        )

        # Add dropdown
        self.figure.update_layout(
            updatemenus=[
                dict(
                    buttons=list(
                        [
                            dict(
                                args=[{"visible": [True, False, True]}],
                                label="All Portfolios",
                                method="update",
                            ),
                            dict(
                                args=[{"visible": [False, True, True]}],
                                label="Better than market",
                                method="update",
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
                    active=0,
                    # ),
                ),
            ]
        )
        self.figure.update_layout(showlegend=False)
        return self.figure, age_categories

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
                marker_colors=px.colors.qualitative.G10,
                hoverinfo="skip",
            )
        )

        return self.figure
