import plotly.express as px
from datetime import date
import plotly.graph_objects as go
import pandas as pd
import numpy as np


project = "Figure Friday 2025 - week 37 "
project_title = "Amazon Catalog Performance: A Dual Perspective on Sales and Risk"
date = date(2025, 9, 19)
detail_project = "What type of products were sold on Amazon?"
dataset_url = "https://community.plotly.com/t/figure-friday-2025-week-37/94168"

download_url = "dataset/amazon_sales_data.csv"


class BubbleChartPlotly:
    def __init__(
        self, labels, area, original_sales, colors, bubble_spacing=1, plot_height=700
    ):
        self.labels = labels
        self.colors = colors
        self.area = np.asarray(area)
        self.original_sales = original_sales

        self.plot_height = plot_height
        self.plot_radius = plot_height / 2.7
        self.bubble_spacing = bubble_spacing

        self.radii = np.sqrt(self.area / np.pi)
        self.scale_factor = (plot_height * 0.166) / self.radii.max()
        self.scaled_radii = self.radii * self.scale_factor
        self.scaled_area = np.pi * (self.scaled_radii**2)

        self.bubbles = np.ones((len(area), 4))
        self.bubbles[:, 2] = self.scaled_radii
        self.bubbles[:, 3] = self.scaled_area
        self.maxstep = 2 * self.bubbles[:, 2].max() + self.bubble_spacing
        self.step_dist = self.maxstep / 1.8
        length = np.ceil(np.sqrt(len(self.bubbles)))
        grid = np.arange(length) * self.maxstep
        gx, gy = np.meshgrid(grid, grid)
        self.bubbles[:, 0] = gx.flatten()[: len(self.bubbles)]
        self.bubbles[:, 1] = gy.flatten()[: len(self.bubbles)]
        self.com = self.center_of_mass()

    def center_of_mass(self):
        return np.average(self.bubbles[:, :2], axis=0, weights=self.bubbles[:, 3])

    def center_distance(self, bubble, bubbles):
        return np.hypot(bubble[0] - bubbles[:, 0], bubble[1] - bubbles[:, 1])

    def outline_distance(self, bubble, bubbles):
        return (
            self.center_distance(bubble, bubbles)
            - bubble[2]
            - bubbles[:, 2]
            - self.bubble_spacing
        )

    def check_collisions(self, bubble, bubbles):
        distance = self.outline_distance(bubble, bubbles)
        return len(distance[distance < 0])

    def collides_with(self, bubble, bubbles):
        distance = self.outline_distance(bubble, bubbles)
        return np.argmin(distance, keepdims=True)

    def collapse(self, n_iterations=100):
        for _ in range(n_iterations):
            moves = 0
            for i in range(len(self.bubbles)):
                rest_bub = np.delete(self.bubbles, i, 0)
                dir_vec = self.com - self.bubbles[i, :2]
                norm = np.linalg.norm(dir_vec)
                if norm == 0:
                    continue
                dir_vec = dir_vec / norm
                new_point = self.bubbles[i, :2] + dir_vec * self.step_dist
                new_bubble = np.append(new_point, self.bubbles[i, 2:4])

                if not self.check_collisions(new_bubble, rest_bub):
                    self.bubbles[i, :] = new_bubble
                    self.com = self.center_of_mass()
                    moves += 1
                else:
                    for colliding in self.collides_with(new_bubble, rest_bub):
                        dir_vec = rest_bub[colliding, :2] - self.bubbles[i, :2]
                        norm = np.linalg.norm(dir_vec)
                        if norm == 0:
                            continue
                        dir_vec = dir_vec / norm
                        orth = np.array([dir_vec[1], -dir_vec[0]])
                        new_point1 = self.bubbles[i, :2] + orth * self.step_dist
                        new_point2 = self.bubbles[i, :2] - orth * self.step_dist
                        dist1 = self.center_distance(self.com, np.array([new_point1]))
                        dist2 = self.center_distance(self.com, np.array([new_point2]))
                        new_point = new_point1 if dist1 < dist2 else new_point2
                        new_bubble = np.append(new_point, self.bubbles[i, 2:4])
                        if not self.check_collisions(new_bubble, rest_bub):
                            self.bubbles[i, :] = new_bubble
                            self.com = self.center_of_mass()
            if moves / len(self.bubbles) < 0.05:
                self.step_dist /= 2

    def to_dataframe(self):
        return pd.DataFrame(
            {
                "x": self.bubbles[:, 0],
                "y": self.bubbles[:, 1],
                "radius": self.bubbles[:, 2],
                "scaled_area": self.bubbles[:, 3],
                "label": self.labels,
                "color": self.colors,
                "original_sales": self.original_sales,
            }
        )


def graphBar(template):
    try:
        df = pd.read_csv(download_url)
    except FileNotFoundError:
        print(
            f"Error: El archivo '{download_url}' no se encontró. Asegúrate de que esté en el directorio correcto."
        )
        exit()
    df_agg = (
        df.groupby(["Category", "Status"])
        .agg(order_count=("Order ID", "size"))
        .reset_index()
    )
    total_sales_cancelled = df[df["Status"] == "Cancelled"]["Total Sales"].sum()
    total_sales_completed = df[df["Status"] == "Completed"]["Total Sales"].sum()
    total_sales_pending = df[df["Status"] == "Pending"]["Total Sales"].sum()
    color_map = {"Completed": "#30d673", "Pending": "#dadada", "Cancelled": "#c85b5b"}

    fig = go.Figure()

    for status, color in color_map.items():
        subset = df_agg[df_agg["Status"] == status]
        x_data = subset["order_count"].apply(
            lambda x: x if status != "Cancelled" else -x
        )
        fig.add_trace(
            go.Bar(
                y=subset["Category"],
                x=x_data,
                name=status,
                orientation="h",
                marker_color=color,
                hovertemplate="%{y}<br><b>Number of orders:</b> %{customdata:,.0f}<extra></extra>",
                customdata=subset["order_count"],
                width=0.4,
            )
        )

    fig.update_layout(
        barmode="relative",
        template=template,
        xaxis_title="Number of Orders",
        yaxis_title="Category",
        bargap=0.01,
        legend_title_text="Status type",
        margin=dict(l=150, b=100, t=100, r=10),
        height=500,
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=[-(x) for x in range(0, 90, 10)] + list(range(0, 90, 10)),
        ticktext=[str(x) for x in range(0, 90, 10)]
        + [str(x) for x in range(10, 90, 10)],
        range=[-91, 91],
    )

    annotations = [
        dict(
            xref="paper",
            yref="paper",
            x=0.1,
            y=1.05,
            xanchor="left",
            yanchor="bottom",
            text=f"<b>Canceled:</b><br>${total_sales_cancelled}",
            font=dict(size=12, color=color_map["Cancelled"]),
            # bgcolor="rgba(0,0,0,0.5)",
            bordercolor=color_map["Cancelled"],
            borderwidth=1,
            borderpad=4,
        ),
        dict(
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.05,
            xanchor="center",
            yanchor="bottom",
            text=f"<b>Completed:</b><br>${total_sales_completed}",
            font=dict(size=12, color=color_map["Completed"]),
            # bgcolor="rgba(0,0,0,0.5)",
            bordercolor=color_map["Completed"],
            borderwidth=1,
            borderpad=4,
        ),
        dict(
            xref="paper",
            yref="paper",
            x=0.9,
            y=1.05,
            xanchor="right",
            yanchor="bottom",
            text=f"<b>Pending:</b><br>${total_sales_pending}",
            font=dict(
                size=12,
                color="grey" if template == "plotly_white" else color_map["Pending"],
            ),
            # bgcolor="rgba(0,0,0,0.5)",
            bordercolor=color_map["Pending"],
            borderwidth=1,
            borderpad=4,
        ),
    ]

    fig.update_layout(annotations=annotations)
    return fig


def graphBubble(template):
    try:
        df = pd.read_csv(download_url)
    except FileNotFoundError:
        print(
            f"Error: El archivo '{download_url}' no se encontró. Asegúrate de que esté en el directorio correcto."
        )
        exit()

    def plot_bubble_chart_plotly(df, plot_height=700, template="plotly_white"):
        chart = BubbleChartPlotly(
            labels=df["label"],
            area=df["size"],
            original_sales=df["original_sales"],
            colors=df["color"],
            bubble_spacing=2,
            plot_height=plot_height,
        )
        chart.collapse()
        df_bubbles = chart.to_dataframe()
        df_bubbles["size_px"] = df_bubbles["radius"] * 2

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_bubbles["x"],
                y=df_bubbles["y"],
                mode="markers+text",
                marker=dict(
                    size=df_bubbles["size_px"],
                    color=df_bubbles["color"],
                    sizemode="diameter",
                    opacity=0.9,
                ),
                text=df_bubbles["label"],
                textposition="middle center",
                textfont=dict(
                    size=np.clip(
                        df_bubbles["scaled_area"]
                        / df_bubbles["scaled_area"].max()
                        * 24,
                        5,
                        18,
                    )
                ),
                hovertemplate=(
                    "<b>Product:</b> %{customdata[0]}<br>"
                    + "<b>Total sales:</b> $%{customdata[1]:,.0f}"
                    + "<extra></extra>"
                ),
                customdata=df_bubbles[["label", "original_sales"]],
            )
        )

        fig.update_layout(
            template=template,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=100, r=100, t=0, b=0),
            height=plot_height,
            # width=plot_height,
            autosize=True,
        )

        return fig

    df_grouped = df.groupby("Product")["Total Sales"].sum().reset_index()
    n_products = len(df_grouped)
    colors_list = px.colors.qualitative.Plotly[:n_products]
    color_map = {
        product: colors_list[i]
        for i, product in enumerate(df_grouped["Product"].unique())
    }
    df_grouped["color"] = df_grouped["Product"].map(color_map)
    df_to_plot = pd.DataFrame(
        {
            "label": df_grouped["Product"],
            "size": df_grouped["Total Sales"],
            "original_sales": df_grouped["Total Sales"],
            "color": df_grouped["color"],
        }
    )
    return plot_bubble_chart_plotly(df_to_plot, plot_height=500, template=template)


plots = [
    {
        "title": "Order Distribution by Status & Category.",
        "subtitle": "Analyzes order volume by product category and status (completed, pending, canceled), including total revenue per status.",
        "graph": graphBar,
    },
    {
        "title": "Product Sales Analysis: Visualized Market Share.",
        "subtitle": "This bubble chart represents each product's visual market share based on its total sales. The size of each bubble indicates the magnitude of sales, offering a direct visual comparison between products.",
        "graph": graphBubble,
    },
]
