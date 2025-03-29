from random import random

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import holidays
import datetime


# ---------------------------------------------
# Funkcje pomocnicze
# ---------------------------------------------
def create_dash(flask_app):

    def get_free_days(start_date, end_date):
        pl_holidays = holidays.Poland(years=range(start_date.year, end_date.year + 1))
        date_range = pd.date_range(start=start_date, end=end_date)
        return [date for date in date_range if date.weekday() >= 5 or date in pl_holidays]

    def load_hois_map():
        file_path = "hois_map.csv"
        hois_df = pd.read_csv(file_path, encoding="utf-8", sep=";")
        hois_df.columns = [col.strip() for col in hois_df.columns]
        expected_columns = ["HOIS", "Grupa towarowa", "Grupa sklepowa"]
        actual_columns = hois_df.columns.tolist()
        if len(actual_columns) != len(expected_columns):
            raise Exception(f"Plik CSV powinien mieć kolumny: {expected_columns}, ale znaleziono: {actual_columns}")
        return {row["HOIS"]: (row["Grupa towarowa"], row["Grupa sklepowa"]) for _, row in hois_df.iterrows()}

    def load_data():
        files = ["data01.xlsx", "data02.xlsx", "data03.xlsx"]
        dfs = []
        for file in files:
            try:
                df_month = pd.read_excel(file)
                if "Data" not in df_month.columns:
                    print(f"Błąd: W pliku {file} brak kolumny 'Data'")
                    continue
                df_month["Data_full"] = pd.to_datetime(df_month["Data"], errors="coerce")
                df_month["Data"] = df_month["Data_full"].dt.date
                dfs.append(df_month)
            except Exception as e:
                print(f"Błąd przy wczytywaniu {file}: {e}")
        if not dfs:
            raise Exception("Brak poprawnych danych do połączenia!")
        df = pd.concat(dfs, ignore_index=True)
        df = df.dropna(subset=["Data_full"])
        return df

    # ---------------------------------------------
    # Wczytanie danych
    # ---------------------------------------------
    hois_map = load_hois_map()
    df = load_data()

    # Mapowanie dodatkowych kolumn
    df["Grupa towarowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[0])
    df["Grupa sklepowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[1])

    # Ustalenie zakresu dat i opcji do filtrów
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    station_options = df["Stacja"].unique().tolist()
    group_options = df["Grupa towarowa"].unique().tolist()

    # ---------------------------------------------
    # Layout aplikacji Dash
    # ---------------------------------------------
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        server = flask_app,
        url_base_pathname = "/dashboard/"
    )


    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Filtry"),
                html.Label("Zakres dat"),
                dcc.DatePickerRange(
                    id='date-picker',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date,
                    end_date=max_date,
                    display_format='YYYY-MM-DD'
                ),
                html.Br(), html.Br(),
                html.Label("Stacje:"),
                dcc.Dropdown(
                    id='station-dropdown',
                    options=[{'label': s, 'value': s} for s in station_options],
                    value=station_options,
                    multi=True
                ),
                html.Br(),
                html.Label("Grupy towarowe:"),
                dcc.Dropdown(
                    id='group-dropdown',
                    options=[{'label': g, 'value': g} for g in group_options],
                    value=group_options,
                    multi=True
                ),
                html.Br(),
                dcc.Checklist(
                    id='monthly-check',
                    options=[{'label': 'Widok miesięczny według stacji', 'value': 'monthly'}],
                    value=[]
                )
            ], width=3),
            dbc.Col([
                dcc.Tabs(id='tabs', value='tab1', children=[
                    dcc.Tab(label='Ogólny', value='tab1'),
                    dcc.Tab(label='Sklep', value='tab2'),
                    dcc.Tab(label='Paliwo', value='tab3'),
                    dcc.Tab(label='Lojalność', value='tab4'),
                    dcc.Tab(label='Myjnia', value='tab5'),
                    dcc.Tab(label='Ulubione', value='tab6'),
                    dcc.Tab(label='Sprzedaż per kasjer', value='tab7')
                ]),
                html.Div(id='tabs-content', style={'marginTop': '20px'})
            ], width=9)
        ])
    ], fluid=True)

    # ---------------------------------------------
    # Callback renderujący zawartość zakładki
    # ---------------------------------------------
    @app.callback(
        Output('tabs-content', 'children'),
        Input('tabs', 'value'),
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('station-dropdown', 'value'),
        Input('group-dropdown', 'value'),
        Input('monthly-check', 'value')
    )
    def render_tab_content(tab, start_date, end_date, selected_stations, selected_groups, monthly_check):
        # Filtrowanie danych
        start_date_obj = pd.to_datetime(start_date).date()
        end_date_obj = pd.to_datetime(end_date).date()
        dff = df[(df["Data"] >= start_date_obj) &
                 (df["Data"] <= end_date_obj) &
                 (df["Stacja"].isin(selected_stations)) &
                 (df["Grupa towarowa"].isin(selected_groups))].copy()
        dff = dff[dff["Login POS"] != 99999].copy()

        # Ustalenie okresu: dzienne lub miesięczne
        if 'monthly' in monthly_check:
            dff["Okres"] = pd.to_datetime(dff["Data"]).dt.to_period("M").astype(str)
            category_col = "Stacja"
        else:
            dff["Okres"] = dff["Data"]
            category_col = None

        if tab == 'tab1':
            # Przykładowe metryki
            total_netto = dff["Netto"].sum()
            total_transactions = dff["#"].nunique()
            kawa_netto = dff[dff["Grupa sklepowa"] == "NAPOJE GORĄCE"]["Netto"].sum()
            food_netto = dff[dff["Grupa towarowa"].str.strip().str.upper().isin(["FOOD SERVICE", "USLUGI DODATKOWE"])]["Netto"].sum()
            myjnia_netto = dff[dff["Grupa sklepowa"] == "MYJNIA INNE"]["Netto"].sum()

            # Wykres obrotu netto
            grouped_netto = dff.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index()
            fig_netto = px.line(grouped_netto, x="Okres", y="Netto", color=category_col, title="Obrót netto (NFR+Fuel)", markers=True)

            # Wykres liczby transakcji
            grouped_tx = dff.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index()
            fig_tx = px.line(grouped_tx, x="Okres", y="#", color=category_col, title="Liczba transakcji", markers=True)

            # Dodanie pionowych linii dla dni wolnych
            try:
                start_dt = pd.to_datetime(dff["Okres"].min())
                end_dt = pd.to_datetime(dff["Okres"].max())
                free_days = get_free_days(start_dt, end_dt)
                for day in free_days:
                    fig_netto.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
                    fig_tx.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            except Exception as e:
                print("Błąd przy dodawaniu dni wolnych: ", e)

            content = html.Div([
                html.H3("Ogólny"),
                html.Div([
                    html.Div(f"Obrót netto (NFR+Fuel): {total_netto/1_000_000:.1f} mln zł", style={'display': 'inline-block', 'marginRight': '20px', 'color': 'red'}),
                    html.Div(f"Unikalne transakcje: {total_transactions/1000:,.0f} tys.", style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż kawy: {round(kawa_netto/1000):,} tys. zł", style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż food: {round(food_netto/1000):,} tys. zł", style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż myjni: {round(myjnia_netto/1000):,} tys. zł", style={'display': 'inline-block'})
                ], style={'marginBottom': '20px'}),
                dcc.Graph(figure=fig_netto),
                dcc.Graph(figure=fig_tx),
                html.H4("Heatmapa transakcji – dzień tygodnia vs godzina"),
                # Tutaj możesz dodać dodatkową logikę dla heatmapy – np. wybór metryki i odpowiednie przetwarzanie danych.
                dcc.Graph(figure={})
            ])
            return content
        else:
            # Inne zakładki – przykładowy placeholder
            return html.Div([html.H3(f"Zakładka: {tab}"), html.P("Implementację pozostałych widoków uzupełnij analogicznie.")])
    return app
    # ---------------------------------------------
    # Uruchomienie aplikacji
    # ---------------------------------------------

