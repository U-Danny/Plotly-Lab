# app.py
import dash
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import os
import importlib.util
from datetime import date
from dash import callback_context as ctx
import pandas as pd

FONT_LINK = "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    FONT_LINK,
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    dbc.icons.FONT_AWESOME,
    dbc.icons.BOOTSTRAP,
]

config = {
    "displaylogo": False,
    "modeBarButtonsToAdd": [
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
    ],
    "responsive": True,
}

VIZ_DIR = "viz"


def load_visualizations_data():
    """
    Carga dinámicamente los datos de cada módulo de visualización.
    Retorna un diccionario con los datos, ordenados por fecha descendente.
    """
    visualizations_data = {}
    if not os.path.isdir(VIZ_DIR):
        print(f"Error: El directorio '{VIZ_DIR}' no existe.")
        return visualizations_data

    for filename in os.listdir(VIZ_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(VIZ_DIR, filename)

            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                visualizations_data[module_name] = {
                    "project": getattr(module, "project", "Proyecto Desconocido"),
                    "project_title": getattr(
                        module,
                        "project_title",
                        getattr(module, "project", "Proyecto Desconocido"),
                    ),
                    "date": getattr(module, "date", date.min),
                    "detail_project": getattr(
                        module, "detail_project", "Sin detalles."
                    ),
                    "dataset_url": getattr(module, "dataset_url", "#"),
                    "plots": getattr(module, "plots", []),
                }
            except Exception as e:
                print(f"No se pudo cargar el módulo '{module_name}': {e}")

    sorted_viz = sorted(
        visualizations_data.items(), key=lambda item: item[1]["date"], reverse=True
    )
    return {k: v for k, v in sorted_viz}


all_viz_data = load_visualizations_data()
available_viz_keys = list(all_viz_data.keys())
initial_viz_key = available_viz_keys[0] if available_viz_keys else None
initial_viz = all_viz_data.get(initial_viz_key, {})

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    title="Figure Friday 2025",
    assets_folder="assets",
    update_title=None,
    suppress_callback_exceptions=True,
)

app.layout = dbc.Container(
    [
        dcc.Store(id="theme-store", data="dark"),
        dcc.Store(id="current-viz-store", data={"key": initial_viz_key, "index": 0}),
        # Contenedor de la cabecera
        html.Div(
            [
                html.Div(
                    [
                        dbc.Button(
                            html.I(className="fa-solid fa-circle-info"),
                            id="btn-download",
                            color="link",
                            className="me-2 px-1 p-0 text-secondary",
                            title="Information",
                        ),
                        dbc.Button(
                            html.I(className="fa-solid fa-expand"),
                            id="fullscreen-btn",
                            color="link",
                            className="me-2 p-0 text-secondary",
                            title="Fullscreen",
                        ),
                        dbc.Button(
                            html.I(id="icon-theme", className="fa-solid fa-moon"),
                            id="btn-theme-switch",
                            className="p-0 text-secondary",
                            color="link",
                            title="Theme",
                            n_clicks=0,
                        ),
                    ],
                    id="icon-buttons",
                    className="pt-1 ",
                ),
                html.Div(
                    [
                        dbc.DropdownMenu(
                            id="viz-selector-dropdown-menu",
                            label="Seleccionar Proyecto",
                            children=[
                                dbc.DropdownMenuItem(
                                    data["project"],
                                    id={"type": "viz-item", "index": key},
                                )
                                for key, data in all_viz_data.items()
                            ],
                            color="secondary",
                            size="sm",
                            className="dropdown-responsive",
                        ),
                    ],
                ),
            ],
            # Contenedor para los botones
            id="header-container",
            className="container pt-1 pb-2",
            style={
                "display": "flex",
                "justifyContent": "space-between",
            },
        ),
        # Uso de flex-wrap para responsividad
        html.H4(
            id="header-title",
            style={"fontWeight": "700"},
            className="container",  # Margen izquierdo y superior para separarlo
        ),
        html.Div(
            [
                dbc.Progress(
                    value=0,
                    style={"height": "3px"},
                    color="primary",
                    className="mb-1 w-100",
                    id="id-counter",
                ),
            ],
            className="my-0 py-0 pb-1 container",
        ),
        # Línea divisoria
        # Contenedor principal con los gráficos
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # Botones en fila arriba
                                html.Div(
                                    [
                                        dbc.Button(
                                            html.I(id="icon-prev", className="fa-xl"),
                                            id="prev",
                                            color="link",
                                            n_clicks=0,
                                            className="p-0 me-2",
                                        ),
                                        dbc.Button(
                                            html.I(
                                                id="icon-next", className="fa-2x"
                                            ),  # botón derecho más grande
                                            id="next",
                                            color="link",
                                            n_clicks=0,
                                            className="p-0",
                                        ),
                                    ],
                                    className="d-flex pb-0",
                                ),
                                # Contador debajo de los botones
                                html.Small(
                                    id="count-plot",
                                    className="fw-bold my-0 py-0",
                                    style={"fontSize": "10px"},
                                ),
                            ],
                            width="auto",
                            className="",
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H5(
                                            id="title-plot",
                                            className="fw-bold my-0 text-wrap",  # Agregado text-wrap
                                            style={"fontSize": "18px"},
                                        ),
                                        html.H6(
                                            id="sub-title-plot",
                                            className="text-wrap my-0 pt-2",
                                            style={"fontSize": "14px"},
                                        ),
                                    ],
                                    className="d-flex flex-column align-items-start",
                                ),
                            ],
                            className="me-auto",  # Eliminado width="auto"
                        ),
                    ],
                    className="my-2",
                ),
            ],
            className="container",
        ),
        html.Hr(className="container my-0 py-0 text-secondary"),
        html.Div(
            [
                # Lado izquierdo (título, subtítulo y flechas)
                # Lado derecho (contenedor del plot)
                html.Div(
                    [
                        dcc.Loading(
                            id="id-plots",
                            color="#018E99",
                            type="cube",
                            style={"marginTop": "120px"},
                        ),
                    ],
                    id="plot-container",
                    className="flex-grow-1",
                    style={"height": "100%", "width": "100%"},
                ),
            ],
            id="main-content-container",
            className="container pt-2 py-0 my-0",
            style={
                "fontFamily": "'Roboto', sans-serif",
                "min-height": "calc(100vh - 250px)",
            },
        ),
        # Footer
        html.Div(
            [
                html.Span(
                    [
                        "© - 2025 ",
                        html.A(
                            "UD-Git.",
                            href="https://github.com/U-Danny/Plotly-Lab",
                            target="_blank",
                            style={"color": "inherit", "textDecoration": "underline"},
                        ),
                    ],
                    style={"flex": "1", "textAlign": "left"},
                ),
                html.Span(
                    "Figure Friday 2025", style={"flex": "1", "textAlign": "right"}
                ),
            ],
            className="container",
            style={
                "fontSize": "12px",
                "color": "#888",
                "padding": "8px",
                "marginTop": "20px",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            },
        ),
        dbc.Modal(
            [
                dbc.ModalBody(id="modal-body-content"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Cerrar",
                        id="close-modal-btn",
                        n_clicks=0,
                        className="ms-auto",
                    )
                ),
            ],
            id="download-modal",
            size="lg",
            is_open=False,
            centered=True,
        ),
    ],
    fluid=True,
    id="page-container",
    style={
        "minHeight": "100vh",
        "height": "100%",
        "width": "100%",
        "flexGrow": 1,
        "padding": "0px",
    },
)

# --- Callbacks ---


# Callback para el modal de descarga (Data info)
@app.callback(
    Output("download-modal", "is_open"),
    Output("modal-body-content", "children"),
    Input("btn-download", "n_clicks"),
    Input("close-modal-btn", "n_clicks"),
    State("download-modal", "is_open"),
    State("current-viz-store", "data"),
)
def toggle_download_modal(n_clicks_open, n_clicks_close, is_open, current_viz_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "btn-download":
        viz_key = current_viz_data["key"]
        project_data = all_viz_data.get(viz_key, {})

        # Contenido del cuerpo del modal
        body_content = [
            html.H4(f"{project_data.get('project', 'N/A')}", className="mb-3"),
            html.P(f"{project_data.get('detail_project', 'N/A')}"),
            html.P(
                [
                    "",
                    html.A(
                        project_data.get("dataset_url", "#"),
                        href=project_data.get("dataset_url", "#"),
                        target="_blank",
                    ),
                ]
            ),
        ]
        return not is_open, body_content
    elif trigger_id == "close-modal-btn":
        return False, dash.no_update

    return is_open, dash.no_update


# Callback para actualizar el dcc.Store
@app.callback(
    Output("current-viz-store", "data"),
    Input({"type": "viz-item", "index": dash.ALL}, "n_clicks"),
    Input("prev", "n_clicks"),
    Input("next", "n_clicks"),
    State("current-viz-store", "data"),
    prevent_initial_call=True,
)
def update_current_viz(n_clicks_dropdown, prev_clicks, next_clicks, current_viz_data):
    trigger = ctx.triggered[0]
    trigger_id = trigger["prop_id"]

    current_key = current_viz_data.get("key")
    current_index = current_viz_data.get("index", 0)

    if "viz-item" in trigger_id:
        triggered_id = trigger["prop_id"].split(".")[-2].split('"')[3]
        new_key = triggered_id
        new_index = 0
        return {"key": new_key, "index": new_index}

    if "next" in trigger_id:
        plots_array = all_viz_data.get(current_key, {}).get("plots", [])
        if current_index < len(plots_array) - 1:
            current_index += 1
    elif "prev" in trigger_id:
        if current_index > 0:
            current_index -= 1

    return {"key": current_key, "index": current_index}


# Callback para actualizar la UI completa
@app.callback(
    [
        Output("id-plots", "children"),
        Output("title-plot", "children"),
        Output("sub-title-plot", "children"),
        Output("prev", "disabled"),
        Output("next", "disabled"),
        Output("count-plot", "children"),
        Output("id-counter", "value"),
        Output("page-container", "style"),
        Output("header-title", "children"),
        Output("icon-prev", "className"),
        Output("icon-next", "className"),
        Output("icon-theme", "className"),
    ],
    [
        Input("current-viz-store", "data"),
        Input("btn-theme-switch", "n_clicks"),
    ],
    [
        State("page-container", "style"),
    ],
)
def update_ui(current_viz_data, switch_value, page_style):
    if switch_value is None:
        switch_value = 0
    theme = "light" if switch_value % 2 == 0 else "dark"
    template = "plotly_dark" if theme == "dark" else "none"

    viz_key = current_viz_data["key"]
    plot_index = current_viz_data["index"]

    viz_data = all_viz_data.get(viz_key, {})
    plots = viz_data.get("plots", [])

    if not plots:
        return (
            html.Div(
                html.H5("No hay visualizaciones disponibles."),
                style={"textAlign": "center"},
            ),
            "No hay datos",
            "N/A",
            True,
            True,
            "0 of 0",
            0,
            dash.no_update,
            "Sin proyecto",
            "fa-solid fa-circle-arrow-left fa-xl",
            "fa-solid fa-circle-arrow-right fa-3x",
            "fa-solid fa-moon",
        )

    current_plot = plots[plot_index]
    fig = current_plot["graph"](template)

    plot_div = html.Div(
        [
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={
                    # El componente ocupa todo el ancho del div padre
                    "width": "100%",
                    "height": "100%",
                },
            )
        ],
        # El div padre se encarga de centrar el contenido
        className="d-flex justify-content-center",
        style={
            "width": "100%",
            "height": "100%",
        },
    )
    max_index = len(plots) - 1
    active_prev = plot_index == 0
    active_next = plot_index == max_index

    progreso_porcentual = ((plot_index + 1) / len(plots)) * 100
    count_text = f"{plot_index + 1} de {len(plots)}"

    page_bg = "#121212" if theme == "dark" else "#ffffff"
    text_color = "white" if theme == "dark" else "#212529"
    new_page_style = page_style.copy() if page_style else {}
    new_page_style.update({"backgroundColor": page_bg, "color": text_color})

    prev_class = f"fa-solid fa-circle-arrow-left fa-xl {'text-light' if theme == 'dark' else 'text-dark'}"
    next_class = f"fa-solid fa-circle-arrow-right fa-3x {'text-light' if theme == 'dark' else 'text-dark'}"
    icon_theme = "fa-solid fa-moon" if theme == "dark" else "fa-solid fa-sun"

    # Aquí es donde se usa el nuevo project_title
    project_title_display = viz_data.get(
        "project_title", viz_data.get("project", "Proyecto Desconocido")
    )

    return (
        plot_div,
        current_plot["title"],
        current_plot["subtitle"],
        active_prev,
        active_next,
        count_text,
        progreso_porcentual,
        new_page_style,
        project_title_display,
        prev_class,
        next_class,
        icon_theme,
    )


# Callback para el estilo del Dropdown
@app.callback(
    Output("viz-selector-dropdown-menu", "label"),
    Output("viz-selector-dropdown-menu", "className"),
    Input("current-viz-store", "data"),
    Input("btn-theme-switch", "n_clicks"),
)
def update_dropdown_label(current_viz_data, n_clicks):
    viz_key = current_viz_data["key"]
    project_name = all_viz_data.get(viz_key, {}).get("project", "Proyecto Desconocido")

    if n_clicks is None:
        n_clicks = 0
    theme = "light" if n_clicks % 2 == 0 else "dark"

    dropdown_class = "dropdown-responsive"
    if theme == "dark":
        dropdown_class += " dark-mode-dropdown"

    return project_name, dropdown_class


# Callback para actualizar la altura del gráfico
app.clientside_callback(
    """
    function updateGraphHeight(plot_div) {
        // Asegura que el plot-container exista
        const plotContainer = document.getElementById('plot-container');
        if (plotContainer) {
            // Establece la altura del dcc.Graph para que llene el contenedor
            plotContainer.style.height = '100%';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("id-plots", "children", allow_duplicate=True),
    Input("id-plots", "children"),
    prevent_initial_call=True,
)

server = app.server

if __name__ == "__main__":
    app.run(debug=True)
