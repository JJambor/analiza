import abc

from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash
from main.core.dash_app import DashApp
from main.dicts.tabs_dict import tabs_dict
from main.enums.tabs import Tabs
from main.utils.utils_functions import *
from main.templates.templates import create_templates

from main.utils.utils_functions import format_metric_value

from main.utils.utils_functions import get_last_day


class DashLayout():
    app: DashApp = None
    dash_app: dash.Dash = None

    def __init__(self, app):
        self.app = app
        self.dash_app = app.get_dash_app()
        create_templates()
        self.set_layout()

    def refresh(self, app):
        self.app = app
        self.dash_app = app.get_dash_app()
        create_templates()
        self.set_layout()
    def set_layout(self):
        self.dash_app.layout = dbc.Container([
            dcc.Store(id='theme-store', data={'theme': 'light'}),
            dcc.Store(id="trigger-graph-resize", data={"value": 0}),
            dcc.Interval(id="theme-init", n_intervals=0, max_intervals=1, interval=200),

            dbc.Row([
                dbc.Col(
                    dbc.Button("Pokaż / Ukryj filtry", id="toggle-filter-button", color="primary", n_clicks=0),
                    width="auto"
                ),

                dbc.Col(
                    dbc.Button("🌙", id="theme-toggle-button", color="primary", n_clicks=0, title="Zmień motyw"),
                    width="auto",
                    className="ms-auto text-end"
                )
            ], className="align-items-center mb-3 sticky-header"),

            html.Div([
                html.Div(id="filter-column", children=[
                    html.Div(id="filter-panel", className="", children=[
                        dbc.Card(
                            dbc.CardBody([
                                html.Div([
                                    html.H4("Filtry", className="card-title mb-4"),

                                    # === Zmieniony zakres dat ===
                                    html.Div([
                                        html.Label("Zakres dat", className="form-label"),
                                        html.Div([
                                            html.Div([
                                                html.Div("Od", className="date-label"),
                                                dcc.DatePickerSingle(
                                                    id='start-date',
                                                    min_date_allowed=self.app.get_min_date(),
                                                    max_date_allowed=self.app.get_max_date(),
                                                    date=max(self.app.get_min_date(), get_last_day()),
                                                    display_format='YYYY-MM-DD',
                                                    className="form-control"
                                                )
                                            ], className="date-column"),

                                            html.Div([
                                                html.Div("Do", className="date-label"),
                                                dcc.DatePickerSingle(
                                                    id='end-date',
                                                    min_date_allowed=self.app.get_min_date(),
                                                    max_date_allowed=self.app.get_max_date(),
                                                    date=self.app.get_max_date(),
                                                    display_format='YYYY-MM-DD',
                                                    className="form-control"
                                                )
                                            ], className="date-column")
                                        ], className="date-range-custom d-flex gap-3")
                                    ], className="mb-4"),
                                    # ===========================

                                    html.Div([
                                        html.Label("Stacje:", className="form-label"),
                                        html.Div([
                                            dbc.Button("Zaznacz wszystkie", id='select-all-stations', size="sm",
                                                       color="primary", className="me-2", n_clicks=0),
                                            dbc.Button("Odznacz wszystkie", id='deselect-all-stations', size="sm",
                                                       color="secondary", n_clicks=0),
                                        ], className="mb-2"),
                                        dcc.Dropdown(
                                            id='station-dropdown',
                                            options=[{'label': s, 'value': s} for s in self.app.get_station_options()],
                                            value=self.app.get_station_options(),
                                            multi=True,
                                            className="dropdown-stacje"
                                        )
                                    ], className="mb-4"),

                                    html.Div([
                                        html.Label("Grupy towarowe:", className="form-label"),
                                        html.Div([
                                            dbc.Button("Zaznacz wszystkie", id='select-all-groups', size="sm",
                                                       color="primary", className="me-2", n_clicks=0),
                                            dbc.Button("Odznacz wszystkie", id='deselect-all-groups', size="sm",
                                                       color="secondary", n_clicks=0),
                                        ], className="mb-2"),
                                        dcc.Dropdown(
                                            id='group-dropdown',
                                            options=[{'label': g, 'value': g} for g in self.app.get_group_options()],
                                            value=self.app.get_group_options(),
                                            multi=True,
                                            className="dropdown-grupy"
                                        )
                                    ], className="mb-4"),
                                    html.Div([
                                        html.Label("Produkt (PLU - Nazwa):", className="form-label"),
                                        dcc.Dropdown(
                                            id='product-dropdown',
                                            options=[],
                                            multi=True,
                                            placeholder="Wybierz produkt (opcjonalnie)",
                                            className="dropdown-produkt"
                                        )
                                    ], className="mb-4"),

                                    html.Div([
                                        html.Label("Typ transakcji B2B:", className="form-label"),
                                        dcc.Checklist(
                                            id='b2b-checklist',
                                            options=[
                                                {'label': 'B2B', 'value': 'Tak'},
                                                {'label': 'B2C', 'value': 'Nie'}
                                            ],
                                            value=['Tak', 'Nie'],
                                            className="form-check"
                                        )
                                    ], className="mb-4"),

                                    dcc.Checklist(
                                        id='monthly-check',
                                        options=[{'label': 'Widok miesięczny według stacji', 'value': 'monthly'}],
                                        value=[],
                                        className="form-check"
                                    )
                                ], className="filter-form")
                            ]),
                            className="custom-card"
                        )
                    ])
                ], className="responsive-filter"),

                html.Div(id="content-column", children=[
                    dcc.Tabs(id='tabs', value=Tabs.GENERAL.value, children=[
                        dcc.Tab(label=tabs_dict.get(Tabs.GENERAL), value=Tabs.GENERAL.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.SHOP), value=Tabs.SHOP.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.OIL), value=Tabs.OIL.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.LOYALITY), value=Tabs.LOYALITY.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.WASH), value=Tabs.WASH.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.FAVORITES), value=Tabs.FAVORITES.value),
                        dcc.Tab(label=tabs_dict.get(Tabs.SELL_PER_CASHIER), value=Tabs.SELL_PER_CASHIER.value)
                    ]),
                    dcc.Loading(
                        id="loading-main",
                        type="circle",
                        color="#0F4C81",
                        children=html.Div(id='tabs-content', style={'marginTop': '20px'})
                    )
                ], className="responsive-content")

            ], className="dashboard-layout")

        ], className="main-container", fluid=True, style={"width": "100%"})

    def generate_metric_card(self,label, value, delta=None):
        formatted_value = format_metric_value(value) if isinstance(value, (int, float)) else value
        return html.Div(className="metric-card", children=[
            html.Div(label, className="metric-label"),
            html.Div(formatted_value, className="metric-value"),
            html.Div(delta if delta else "", className=f"metric-delta {'neutral' if not delta else ''}")
        ])

