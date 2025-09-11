import plotly.express as px
from datetime import date
import plotly.graph_objects as go
import pandas as pd
import numpy as np


project = "Figure Friday 2025 - week 36"
project_title = "Dynamic Logistics Analysis of LockerNYC"
date = date(2025, 9, 12)
detail_project = "LockerNYC is a pilot program that allows New Yorkers to receive and send packages using secure lockers on public sidewalks.” What is the distribution of locker sizes in NYC?"
dataset_url = "https://community.plotly.com/t/figure-friday-2025-week-36/94048"

download_url = "dataset/LockerNYC.parquet"


def graphMap(template):
    try:
        df = pd.read_parquet(download_url)
    except FileNotFoundError:
        print(
            f"Error: El archivo '{download_url}' no se encontró. Asegúrate de que esté en el directorio correcto."
        )
        exit()

    df_cleaned = df[
        [
            "Type",
            "Locker Name",
            "Delivery Duration",
            "Created Date",
            "Latitude",
            "longitude",
        ]
    ].copy()
    df_cleaned.dropna(inplace=True)
    df_receives = df_cleaned[df_cleaned["Type"] == "Receive"].copy()

    def duration_to_seconds(duration_str):
        if not isinstance(duration_str, str):
            return None
        try:
            parts = duration_str.split(".")
            days = int(parts[0])
            hours = int(parts[1])
            minutes = int(parts[2])
            seconds = int(parts[3])
            total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
            return total_seconds
        except (ValueError, IndexError):
            return None

    df_receives["Delivery Duration"] = df_receives["Delivery Duration"].apply(
        duration_to_seconds
    )
    df_receives.dropna(subset=["Delivery Duration"], inplace=True)
    if df_receives.empty:
        print(
            "El DataFrame está vacío después de la limpieza de datos. No hay suficientes registros para el análisis."
        )
        exit()
    df_receives["Month"] = (
        pd.to_datetime(df_receives["Created Date"]).dt.to_period("M").astype(str)
    )
    entropy_df_list = []
    all_lockers = df_receives["Locker Name"].unique()
    all_months = sorted(df_receives["Month"].unique())

    for month in all_months:
        month_group = df_receives[df_receives["Month"] == month]

        for locker_name in all_lockers:
            locker_group = month_group[month_group["Locker Name"] == locker_name]
            location = df_receives[df_receives["Locker Name"] == locker_name][
                ["Latitude", "longitude"]
            ].iloc[0]
            if len(locker_group) <= 1:
                entropy_df_list.append(
                    {
                        "Locker Name": locker_name,
                        "Month": month,
                        "Entropy": 0,
                        "Latitude": location["Latitude"],
                        "longitude": location["longitude"],
                    }
                )
                continue
            duration_data = locker_group["Delivery Duration"].astype(float)
            num_bins = "auto"
            if len(duration_data.unique()) < 2:
                num_bins = 1
            hist, bin_edges = np.histogram(duration_data, bins=num_bins)
            prob = hist / hist.sum()
            prob = prob[prob > 0]
            entropy = -np.sum(prob * np.log2(prob))
            entropy_df_list.append(
                {
                    "Locker Name": locker_name,
                    "Month": month,
                    "Entropy": entropy,
                    "Latitude": location["Latitude"],
                    "longitude": location["longitude"],
                }
            )

    entropy_df_animated = pd.DataFrame(entropy_df_list)
    if entropy_df_animated.empty:
        print(
            "No hay suficientes datos para calcular la entropía. No se creará el gráfico."
        )
        exit()
    min_entropy_val = entropy_df_animated["Entropy"].min()
    if min_entropy_val < 0:
        entropy_df_animated["Entropy_transformed"] = (
            entropy_df_animated["Entropy"] - min_entropy_val
        ) ** 2.5 + 1
    else:
        entropy_df_animated["Entropy_transformed"] = (
            entropy_df_animated["Entropy"] ** 2.5 + 1
        )
    fig_map = px.scatter_mapbox(
        entropy_df_animated,
        lat="Latitude",
        lon="longitude",
        color="Entropy",
        size="Entropy_transformed",
        animation_frame="Month",
        hover_name="Locker Name",
        hover_data={
            "Entropy": ":.2f",
            "Month": False,
            "Latitude": False,
            "longitude": False,
        },
        mapbox_style=(
            "carto-darkmatter" if template == "plotly_dark" else "carto-positron"
        ),
        zoom=10,
        height=500,
        color_continuous_scale="Reds" if template == "plotly_dark" else "Bluered",
    )

    fig_map.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox_bounds={"west": -74.26, "east": -73.7, "south": 40.5, "north": 40.92},
        coloraxis_colorbar=dict(title="Entropy"),
    )
    return fig_map


def graphTernary(template):
    try:
        df = pd.read_parquet(download_url)
    except FileNotFoundError:
        print(
            f"Error: El archivo '{download_url}' no se encontró. Asegúrate de que esté en el directorio correcto."
        )
        exit()
    df_receives = df[df["Type"] == "Receive"].copy()
    df_receives.dropna(
        subset=["Locker Size", "Created Date", "Locker Name"], inplace=True
    )
    df_receives["Month"] = (
        pd.to_datetime(df_receives["Created Date"]).dt.to_period("M").astype(str)
    )
    df_receives["Locker Size"] = df_receives["Locker Size"].replace(["L", "XL"], "L-XL")
    locker_proportions = (
        df_receives.groupby(["Month", "Locker Name", "Locker Size"])
        .size()
        .reset_index(name="count")
    )
    locker_proportions["proportion"] = locker_proportions.groupby(
        ["Month", "Locker Name"]
    )["count"].transform(lambda x: 100 * x / x.sum())
    proportions_pivot = (
        locker_proportions.pivot_table(
            index=["Month", "Locker Name"], columns="Locker Size", values="proportion"
        )
        .fillna(0)
        .reset_index()
    )
    required_sizes = ["S", "M", "L-XL"]
    for size in required_sizes:
        if size not in proportions_pivot.columns:
            proportions_pivot[size] = 0
    fig_ternary = px.scatter_ternary(
        proportions_pivot,
        a="S",
        b="M",
        c="L-XL",
        hover_name="Locker Name",
        color="Locker Name",
        hover_data={"S": ":.1f", "M": ":.1f", "L-XL": ":.1f", "Locker Name": False},
        animation_frame="Month",
        # title='Composición de Tamaño de Paquetes por Casillero y Mes',
        height=500,
        template=template,
        size=[5] * len(proportions_pivot),
    )
    fig_ternary.update_layout(
        margin=dict(l=0, r=0, t=50, b=0),
        ternary=dict(
            sum=100,
            aaxis=dict(title="Locker Size S", ticksuffix="%  "),
            baxis=dict(title="Locker Size M", ticksuffix="%  "),
            caxis=dict(title="Locker Size L/XL", ticksuffix="%  "),
        ),
    )
    return fig_ternary


plots = [
    {
        "title": "Entropy Analysis of Smart Lockers in New York City.",
        "subtitle": "A geographical analysis revealing the predictability of package delivery times, visualized by month.",
        "graph": graphMap,
    },
    {
        "title": "Analysis of Package Size Proportions in Smart Lockers.",
        "subtitle": "A dynamic map that shows the composition of packages for each locker, revealing how the mix of sizes (S, M, L/XL) evolves month by month.",
        "graph": graphTernary,
    },
]
