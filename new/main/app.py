from random import random
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
#import plotly.io as pio
import holidays
import datetime
#pio.templates.default = "seaborn"

# ---------------------------------------------
# Funkcje pomocnicze
# ---------------------------------------------
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


def create_dash(flask_app):
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
        server=flask_app,
        url_base_pathname="/dashboard/",
        suppress_callback_exceptions=True  # Added to handle dynamic components
    )

    # Mock session state for favorites
    app.server.config['FAVORITES'] = set()

    app.layout = dbc.Container(children=[
        dbc.Row(children=[
            # FILTRY
            dbc.Col(id="filter-column", children=[
                dbc.Button(
                    "Pokaż / Ukryj filtry", id="toggle-filter-button",
                    color="primary", className="mb-3", n_clicks=0
                ),
                html.Div(id="filter-panel", children=[
                    dbc.Card(
                        dbc.CardBody([
                            html.Div([
                                html.H4("Filtry", className="card-title mb-4"),

                                html.Div([
                                    html.Label("Zakres dat", className="form-label"),
                                    dcc.DatePickerRange(
                                        id='date-picker',
                                        min_date_allowed=min_date,
                                        max_date_allowed=max_date,
                                        start_date=min_date,
                                        end_date=max_date,
                                        display_format='YYYY-MM-DD',
                                        className="form-control"
                                    )
                                ], className="mb-4"),

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
                                        options=[{'label': s, 'value': s} for s in station_options],
                                        value=station_options,
                                        multi=True,
                                        className="form-control"
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
                                        options=[{'label': g, 'value': g} for g in group_options],
                                        value=group_options,
                                        multi=True,
                                        className="form-control"
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
            ], width=3),

            dbc.Col(id="content-column",children=[
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
    ], className="main-container", fluid=True)
    # ---------------------------------------------
    # Callback dla przycisków stacji
    # ---------------------------------------------
    @app.callback(
        Output('station-dropdown', 'value'),
        Input('select-all-stations', 'n_clicks'),
        Input('deselect-all-stations', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_stations(select_all, deselect_all):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'select-all-stations':
                return station_options
            elif button_id == 'deselect-all-stations':
                return []
        return dash.no_update



    # ---------------------------------------------
    # Callback dla przycisków grup towarowych
    # ---------------------------------------------
    @app.callback(
        Output('group-dropdown', 'value'),
        Input('select-all-groups', 'n_clicks'),
        Input('deselect-all-groups', 'n_clicks'),
        prevent_initial_call=True
    )
    def update_groups(select_all, deselect_all):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'select-all-groups':
                return group_options
            elif button_id == 'deselect-all-groups':
                return []
        return dash.no_update

    # ---------------------------------------------
    # Callback renderujący zawartość zakładki
    # ---------------------------------------------
    @app.callback(
        Output('tabs-content', 'children'),
        Input('tabs', 'value'),  # Fixed from 'value_1value' to 'value'
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('station-dropdown', 'value'),
        Input('group-dropdown', 'value'),
        Input('monthly-check', 'value')
    )
    def render_tab_content(tab, start_date, end_date, selected_stations, selected_groups, monthly_check):
        start_date_obj = pd.to_datetime(start_date).date()
        end_date_obj = pd.to_datetime(end_date).date()
        dff = df[(df["Data"] >= start_date_obj) &
                 (df["Data"] <= end_date_obj) &
                 (df["Stacja"].isin(selected_stations)) &
                 (df["Grupa towarowa"].isin(selected_groups))].copy()
        dff = dff[dff["Login POS"] != 99999].copy()

        if 'monthly' in monthly_check:
            dff["Okres"] = pd.to_datetime(dff["Data"]).dt.to_period("M").astype(str)
            category_col = "Stacja"
        else:
            dff["Okres"] = dff["Data"]
            category_col = None

        if tab == 'tab1':
            total_netto = dff["Netto"].sum()
            total_transactions = dff["#"].nunique()
            kawa_netto = dff[dff["Grupa sklepowa"] == "NAPOJE GORĄCE"]["Netto"].sum()
            food_netto = dff[dff["Grupa towarowa"].str.strip().str.upper().isin(["FOOD SERVICE", "USLUGI DODATKOWE"])][
                "Netto"].sum()
            myjnia_netto = dff[dff["Grupa sklepowa"] == "MYJNIA INNE"]["Netto"].sum()

            grouped_netto = dff.groupby(["Okres"] + ([category_col] if category_col else []))[
                "Netto"].sum().reset_index()
            fig_netto = px.line(grouped_netto, x="Okres", y="Netto", color=category_col, title="Obrót netto (NFR+Fuel)",
                                markers=True)

            grouped_tx = dff.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index()
            fig_tx = px.line(grouped_tx, x="Okres", y="#", color=category_col, title="Liczba transakcji", markers=True)

            try:
                start_dt = pd.to_datetime(dff["Okres"].min())
                end_dt = pd.to_datetime(dff["Okres"].max())
                free_days = get_free_days(start_dt, end_dt)
                for day in free_days:
                    fig_netto.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
                    fig_tx.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            except Exception as e:
                print("Błąd przy dodawaniu dni wolnych: ", e)

            return html.Div(children=[
                html.H3("Ogólny"),
                html.Div([
                    html.Div(f"Obrót netto (NFR+Fuel): {total_netto / 1_000_000:.1f} mln zł",
                             style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Unikalne transakcje: {total_transactions / 1000:,.0f} tys.",
                             style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż kawy: {round(kawa_netto / 1000):,} tys. zł",
                             style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż food: {round(food_netto / 1000):,} tys. zł",
                             style={'display': 'inline-block', 'marginRight': '20px'}),
                    html.Div(f"Sprzedaż myjni: {round(myjnia_netto / 1000):,} tys. zł",
                             style={'display': 'inline-block'})
                ], style={'marginBottom': '20px'}),

                dcc.Graph(className="custom-graph",figure=fig_netto),
                dcc.Graph(className="custom-graph",figure=fig_tx),

                html.H4("Heatmapa transakcji – dzień tygodnia vs godzina"),
                dcc.RadioItems(
                    id='metric-selector',
                    options=[
                        {'label': "Liczba transakcji", 'value': "tx"},
                        {'label': "Obrót netto", 'value': "netto"},
                        {'label': "Liczba sztuk", 'value': "ilosc"},
                        {'label': "Transakcje paliwowe", 'value': "paliwo"},
                        {'label': "Penetracja lojalnościowa", 'value': "lojalnosc"}
                    ],
                    value="tx",
                    labelStyle={'display': 'inline-block', 'marginRight': '15px'}
                ),
                dcc.Graph(className="custom-graph",id='heatmap-graph')
            ])

        elif tab == 'tab2':
            netto_bez_hois0 = dff[dff["HOIS"] != 0]["Netto"].sum()
            unikalne_transakcje = dff["#"].nunique()
            avg_transaction = netto_bez_hois0 / unikalne_transakcje if unikalne_transakcje > 0 else 0

            netto_shop_df = dff[dff["HOIS"] != 0].groupby(["Okres"] + ([category_col] if category_col else []))[
                "Netto"].sum().reset_index()
            fig_shop_netto = px.line(netto_shop_df, x="Okres", y="Netto", color=category_col,
                                     title="Obrót sklepowy netto (bez HOIS 0)", markers=True)

            netto_bez_hois0_mies = dff[dff["HOIS"] != 0].groupby("Okres")["Netto"].sum()
            transakcje_all_mies = dff.groupby("Okres")["#"].nunique()
            avg_mies_df = pd.concat([netto_bez_hois0_mies, transakcje_all_mies], axis=1).reset_index()
            avg_mies_df.columns = ["Okres", "Netto_bez_HOIS0", "Transakcje_all"]
            avg_mies_df["Srednia"] = avg_mies_df["Netto_bez_HOIS0"] / avg_mies_df["Transakcje_all"]
            fig_avg_tx = px.line(avg_mies_df, x="Okres", y="Srednia", title="Średnia wartość transakcji", markers=True)

            try:
                start_dt = pd.to_datetime(dff["Okres"].min())
                end_dt = pd.to_datetime(dff["Okres"].max())
                free_days = get_free_days(start_dt, end_dt)
                for day in free_days:
                    fig_shop_netto.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
                    fig_avg_tx.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            except Exception as e:
                print("Błąd przy dodawaniu dni wolnych: ", e)

            df_nonzero_hois = dff[dff["HOIS"] != 0].copy()
            excluded_products = [
                "myjnia jet zafiskalizowana",
                "opłata opak. kubek 0,25zł",
                "myjnia jet żeton"
            ]
            top_products = df_nonzero_hois[
                ~df_nonzero_hois["Nazwa produktu"].str.lower().str.strip().isin(excluded_products)]
            top_products = top_products.groupby("Nazwa produktu")["Ilość"].sum().reset_index()
            top_products = top_products.sort_values(by="Ilość", ascending=False).head(10)

            fig_top_products = None
            if not top_products.empty:
                fig_top_products = px.bar(top_products, x="Nazwa produktu", y="Ilość",
                                          title="Top 10 najlepiej sprzedających się produktów (bez HOIS 0)")

            fig_station_avg = None
            if category_col == "Stacja":
                netto_bez_hois0_stacje = dff[dff["HOIS"] != 0].groupby(["Okres", "Stacja"])["Netto"].sum()
                transakcje_all_stacje = dff.groupby(["Okres", "Stacja"])["#"].nunique()
                avg_mies_stacje_df = pd.concat([netto_bez_hois0_stacje, transakcje_all_stacje], axis=1).reset_index()
                avg_mies_stacje_df.columns = ["Okres", "Stacja", "Netto_bez_HOIS0", "Transakcje_all"]
                avg_mies_stacje_df["Srednia"] = avg_mies_stacje_df["Netto_bez_HOIS0"] / avg_mies_stacje_df[
                    "Transakcje_all"]
                fig_station_avg = px.line(avg_mies_stacje_df, x="Okres", y="Srednia", color="Stacja",
                                          title="Średnia wartość transakcji per stacja", markers=True)
                try:
                    for day in free_days:
                        fig_station_avg.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
                except:
                    pass

            content = [
                html.H3("Sklep"),
                html.Div(children=[
                    html.Div(f"Średnia wartość transakcji: {avg_transaction:.2f} zł",
                             style={'fontWeight': 'bold', 'marginBottom': '20px'})
                ]),
                dcc.Graph(className="custom-graph",figure=fig_shop_netto),
                dcc.Graph(className="custom-graph",figure=fig_avg_tx),
            ]

            if fig_station_avg:
                content.append(dcc.Graph(className="custom-graph",figure=fig_station_avg))

            if fig_top_products:
                content.append(dcc.Graph(className="custom-graph",figure=fig_top_products))
            else:
                content.append(html.Div("Brak danych do wygenerowania wykresu TOP 10.",
                                        style={'color': 'gray', 'fontStyle': 'italic'}))

            return html.Div(content)

        elif tab == 'tab3':
            fuel_df = dff[dff["Grupa sklepowa"] == "PALIWO"]

            if fuel_df.empty:
                return html.Div(children=[
                    html.H3("Paliwo"),
                    html.P("Brak danych paliwowych dla wybranych filtrów.")
                ])

            fuel_sales_grouped = fuel_df.groupby(["Okres"] + ([category_col] if category_col else []))[
                "Ilość"].sum().reset_index()
            fig_fuel_sales = px.line(fuel_sales_grouped, x="Okres", y="Ilość", color=category_col,
                                     title="Sprzedaż paliw", markers=True)

            fuel_df["Typ klienta"] = fuel_df["B2B"].apply(lambda x: "B2B" if str(x).upper() == "TAK" else "B2C")
            customer_types = fuel_df.groupby("Typ klienta")["Ilość"].sum().reset_index()
            fig_customer_types = px.pie(customer_types, values="Ilość", names="Typ klienta",
                                        title="Stosunek tankowań B2C do B2B", hole=0.4)
            fig_customer_types.update_traces(textposition='inside', textinfo='percent+label')

            fuel_sales = fuel_df.groupby("Nazwa produktu")["Ilość"].sum().reset_index()
            fig_fuel_products = px.pie(fuel_sales, names="Nazwa produktu", values="Ilość",
                                       title="Udział produktów paliwowych")

            try:
                start_dt = pd.to_datetime(dff["Okres"].min())
                end_dt = pd.to_datetime(dff["Okres"].max())
                free_days = get_free_days(start_dt, end_dt)
                for day in free_days:
                    fig_fuel_sales.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            except Exception as e:
                print("Błąd przy dodawaniu dni wolnych: ", e)

            return html.Div(children=[
                html.H3("Paliwo"),
                html.H4("Sprzedaż paliw"),
                dbc.Row(children=[
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_fuel_sales), width=12)
                ]),
                dbc.Row(children=[
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_customer_types), width=6),
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_fuel_products), width=6)
                ])
            ])

        elif tab == 'tab4':
            start_date_current = pd.to_datetime(start_date)
            end_date_current = pd.to_datetime(end_date)

            df_loyal_current = dff[
                (dff["Karta lojalnościowa"].str.upper() == "TAK") &
                (pd.to_datetime(dff["Data"]) >= start_date_current) &
                (pd.to_datetime(dff["Data"]) <= end_date_current)
                ]
            df_total_current = dff[
                (pd.to_datetime(dff["Data"]) >= start_date_current) &
                (pd.to_datetime(dff["Data"]) <= end_date_current)
                ]

            penetration_current = 0
            if not df_total_current.empty:
                penetration_current = df_loyal_current["#"].nunique() / df_total_current["#"].nunique() * 100

            start_date_prev = start_date_current - pd.Timedelta(days=30)
            end_date_prev = start_date_current - pd.Timedelta(days=1)

            df_prev_filtered = df[
                (df["Data"] >= start_date_prev.date()) &
                (df["Data"] <= end_date_prev.date())
                ].copy()

            df_prev_filtered["Grupa towarowa"] = df_prev_filtered["HOIS"].map(
                lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[0])
            df_prev_filtered["Grupa sklepowa"] = df_prev_filtered["HOIS"].map(
                lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[1])

            df_prev_filtered = df_prev_filtered[
                (df_prev_filtered["Stacja"].isin(selected_stations)) &
                (df_prev_filtered["Grupa towarowa"].isin(selected_groups)) &
                (df_prev_filtered["Login POS"] != 99999)
                ].copy()

            df_loyal_prev = df_prev_filtered[df_prev_filtered["Karta lojalnościowa"].str.upper() == "TAK"]
            df_total_prev = df_prev_filtered

            penetration_prev = 0
            if not df_total_prev.empty:
                penetration_prev = df_loyal_prev["#"].nunique() / df_total_prev["#"].nunique() * 100

            delta_value = penetration_current - penetration_prev
            prev_label = f"{start_date_prev.strftime('%d.%m')} - {end_date_prev.strftime('%d.%m')}"

            loyalty_df = dff[dff["Karta lojalnościowa"].str.upper() == "TAK"].copy()
            total_df = dff.copy()

            loyal_daily = loyalty_df.groupby("Okres")["#"].nunique().reset_index(name="Lojalnościowe")
            total_daily = total_df.groupby("Okres")["#"].nunique().reset_index(name="Wszystkie")
            merged_df = pd.merge(loyal_daily, total_daily, on="Okres")
            merged_df["Penetracja"] = (merged_df["Lojalnościowe"] / merged_df["Wszystkie"]) * 100

            pl_holidays = holidays.Poland()
            free_days = [day for day in pd.to_datetime(merged_df["Okres"]).dt.date.unique() if
                         day.weekday() >= 5 or day in pl_holidays]

            fig_pen = px.line(merged_df, x="Okres", y="Penetracja", title="Penetracja lojalnościowa (%)")
            fig_pen.update_traces(mode="lines+markers")
            fig_pen.update_layout(xaxis_tickformat="%d.%m")
            for day in free_days:
                fig_pen.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)

            fig_loyal = px.line(loyal_daily, x="Okres", y="Lojalnościowe", title="Transakcje lojalnościowe")
            fig_loyal.update_traces(mode="lines+markers")
            fig_loyal.update_layout(xaxis_tickformat="%d.%m")
            for day in free_days:
                fig_loyal.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)

            df_both = pd.merge(loyal_daily, total_daily, on="Okres")
            df_both_melted = df_both.melt(id_vars=["Okres"], value_vars=["Lojalnościowe", "Wszystkie"],
                                          var_name="Typ transakcji", value_name="Liczba")

            fig_combined = px.line(df_both_melted, x="Okres", y="Liczba", color="Typ transakcji",
                                   title="Transakcje lojalnościowe vs. wszystkie")
            fig_combined.update_traces(mode="lines+markers")
            fig_combined.update_layout(
                xaxis_tickformat="%d.%m",
                yaxis=dict(title="Wszystkie transakcje"),
                yaxis2=dict(title="Lojalnościowe transakcje", overlaying="y", side="right", showgrid=False),
                legend=dict(x=0.01, y=1.15, xanchor="left", yanchor="top", bgcolor='rgba(0,0,0,0)', borderwidth=0)
            )
            fig_combined.for_each_trace(
                lambda trace: trace.update(yaxis="y2") if trace.name == "Lojalnościowe" else None)
            for day in free_days:
                fig_combined.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)

            df_loyal_top = dff[dff["Karta lojalnościowa"].str.upper() == "TAK"].copy()
            total_per_group = dff.groupby("Grupa towarowa")["#"].nunique().reset_index(name="Total")
            loyal_per_group = df_loyal_top.groupby("Grupa towarowa")["#"].nunique().reset_index(name="Lojal")
            merged_top = pd.merge(total_per_group, loyal_per_group, on="Grupa towarowa", how="left")
            merged_top["Lojal"] = merged_top["Lojal"].fillna(0)
            merged_top = merged_top[~merged_top["Grupa towarowa"].str.contains("ZzzGrGSAP")]
            merged_top["Penetracja"] = (merged_top["Lojal"] / merged_top["Total"]) * 100
            merged_top = merged_top.sort_values("Penetracja", ascending=False)
            merged_top["Penetracja"] = merged_top["Penetracja"].round(2).astype(str) + "%"

            return html.Div(children=[
                html.H3("Lojalność"),
                dbc.Row(children=[
                    dbc.Col(children=[
                        html.Div(f"Średnia penetracja (obecny zakres): {penetration_current:.2f}%",
                                 style={'fontWeight': 'bold'}),
                        html.Div(f"Zmiana: {delta_value:.2f}%",
                                 style={'color': 'green' if delta_value > 0 else 'red' if delta_value < 0 else 'gray'})
                    ], width=6),
                    dbc.Col(children=[
                        html.Div(f"Średnia penetracja ({prev_label}): {penetration_prev:.2f}%")
                    ], width=6)
                ], style={'marginBottom': '20px'}),
                dcc.Graph(className="custom-graph",figure=fig_pen),
                dcc.Graph(className="custom-graph",figure=fig_loyal),
                dcc.Graph(className="custom-graph",figure=fig_combined),
                html.H4("TOP / BOTTOM 5 grup towarowych wg penetracji lojalnościowej"),
                dbc.Row(children=[
                    dbc.Col(children=[
                        html.H5("TOP 5"),
                        dash_table.DataTable(
                            data=merged_top.head(5).rename(columns={"Grupa towarowa": "Grupa"}).to_dict('records'),
                            columns=[{"name": "Grupa", "id": "Grupa"},
                                     {"name": "Penetracja", "id": "Penetracja"}],
                            style_table={'overflowX': 'auto'}
                        )
                    ], width=6),
                    dbc.Col(children=[
                        html.H5("BOTTOM 5"),
                        dash_table.DataTable(
                            data=merged_top.tail(5).rename(columns={"Grupa towarowa": "Grupa"}).to_dict('records'),
                            columns=[{"name": "Grupa", "id": "Grupa"},
                                     {"name": "Penetracja", "id": "Penetracja"}],
                            style_table={'overflowX': 'auto'}
                        )
                    ], width=6)
                ])
            ])

        elif tab == 'tab5':
            carwash_df = dff[dff["Grupa sklepowa"] == "MYJNIA INNE"]
            if carwash_df.empty:
                return html.Div(children=[
                    html.H3("Myjnia"),
                    html.P("Brak danych myjni dla wybranych filtrów.")
                ])

            carwash_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[
                "Ilość"].sum().reset_index()
            fig_carwash = px.line(carwash_grouped, x="Okres", y="Ilość", color=category_col,
                                  title="Sprzedaż usług myjni", markers=True)

            sales_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[
                "Netto"].sum().reset_index()
            fig_sales = px.line(sales_grouped, x="Okres", y="Netto", color=category_col,
                                title="Sprzedaż netto grupy Myjnia", markers=True)

            carwash_df["Typ produktu"] = carwash_df["Nazwa produktu"].str.lower().apply(
                lambda x: "Karnet" if x.startswith("karnet") else "Inne")
            pie_df = carwash_df.groupby("Typ produktu")["Ilość"].sum().reset_index()
            fig_karnet = px.pie(pie_df, values="Ilość", names="Typ produktu",
                                title="Udział karnetów w sprzedaży MYJNIA INNE", hole=0.4)
            fig_karnet.update_traces(textposition='inside', textinfo='percent+label')

            def classify_program_all(nazwa):
                nazwa = nazwa.lower()
                if "standard" in nazwa:
                    return "Myjnia Standard"
                elif "express" in nazwa:
                    return "Myjnia Express"
                else:
                    return "Pozostałe"

            carwash_df["Program"] = carwash_df["Nazwa produktu"].apply(classify_program_all)
            program_df_all = carwash_df.groupby("Program")["Ilość"].sum().reset_index()

            fig_program_all = px.pie(
                program_df_all,
                values="Ilość",
                names="Program",
                title="Udział programów Standard i Express w sprzedaży MYJNIA INNE",
                hole=0.4
            )
            fig_program_all.update_traces(textposition='inside', textinfo='percent+label')

            try:
                start_dt = pd.to_datetime(dff["Okres"].min())
                end_dt = pd.to_datetime(dff["Okres"].max())
                free_days = get_free_days(start_dt, end_dt)
                for day in free_days:
                    fig_carwash.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
                    fig_sales.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            except Exception as e:
                print("Błąd przy dodawaniu dni wolnych: ", e)

            return html.Div(children=[
                html.H3("Myjnia"),
                dbc.Row(children=[
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_carwash), width=12)
                ]),
                dbc.Row(children=[
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_sales), width=12)
                ]),
                dbc.Row(children=[
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_karnet), width=6),
                    dbc.Col(dcc.Graph(className="custom-graph",figure=fig_program_all), width=6)
                ])
            ])

        elif tab == 'tab6':
            favorites = app.server.config.get('FAVORITES', set())
            if not favorites:
                return html.Div(children=[
                    html.H3("Ulubione"),
                    html.P("Nie dodano jeszcze żadnych wykresów do ulubionych.")
                ])

            favorite_components = []
            for fav in list(favorites):
                fig = None  # Placeholder; replace with actual figure retrieval logic
                if fig:
                    favorite_components.extend([
                        html.H4(fav),
                        dcc.Graph(className="custom-graph",figure=fig),
                        dbc.Button("✖ Usuń z ulubionych",
                                   id={'type': 'remove-favorite', 'index': fav},
                                   color="danger",
                                   size="sm",
                                   className="mb-3")
                    ])

            return html.Div(children=[
                html.H3("Ulubione wykresy"),
                html.P("Wybrane przez Ciebie wykresy:"),
                *favorite_components
            ])

        elif tab == 'tab7':
            dff["Kasjer"] = dff["Stacja"].astype(str) + " - " + dff["Login POS"].astype(str)

            kasjer_summary = dff.groupby("Kasjer").agg({
                "#": pd.Series.nunique,
                "Netto": "sum",
                "Ilość": "sum"
            }).reset_index()
            kasjer_summary.columns = ["Kasjer", "Liczba transakcji", "Obrót netto", "Suma sztuk"]
            kasjer_summary["Średnia wartość transakcji"] = kasjer_summary["Obrót netto"] / kasjer_summary[
                "Liczba transakcji"]
            kasjer_summary = kasjer_summary.sort_values("Obrót netto", ascending=False)

            top10 = kasjer_summary.head(10)
            fig_kasjer = px.bar(top10, x="Kasjer", y="Obrót netto", title="TOP 10 kasjerów wg obrotu netto")
            fig_trans = px.bar(top10, x="Kasjer", y="Liczba transakcji", title="TOP 10 kasjerów wg liczby transakcji")
            fig_avg = px.bar(top10, x="Kasjer", y="Średnia wartość transakcji",
                             title="TOP 10 kasjerów wg średniej wartości transakcji")

            try:
                top_products_df = pd.read_csv("top_products.csv", sep=";")
                top_products_df["MIESIĄC"] = top_products_df["MIESIĄC"].astype(str)
                top_products_df["PLU"] = top_products_df["PLU"].astype(str)

                dff["Miesiąc"] = pd.to_datetime(dff["Data"]).dt.to_period("M").astype(str)
                dff["PLU"] = dff["PLU"].astype(str)

                dostepne_miesiace = sorted(top_products_df["MIESIĄC"].unique())
                wybrany_miesiac = dostepne_miesiace[-1]

                top_plu_list = top_products_df[top_products_df["MIESIĄC"] == wybrany_miesiac]["PLU"].tolist()
                nazwy_plu = top_products_df.set_index("PLU")["NAZWA"].to_dict()

                df_top = dff[
                    (dff["Miesiąc"] == wybrany_miesiac) &
                    (dff["PLU"].isin(top_plu_list))
                    ].copy()

                if not df_top.empty:
                    df_top["Kasjer"] = df_top["Stacja"].astype(str) + " - " + df_top["Login POS"].astype(str)
                    df_top["PLU_nazwa"] = df_top["PLU"].map(nazwy_plu)
                    sztuki_df = df_top.groupby(["Kasjer", "PLU_nazwa"])["Ilość"].sum().reset_index()

                    fig_top1 = px.bar(
                        sztuki_df,
                        x="Kasjer",
                        y="Ilość",
                        color="PLU_nazwa",
                        title=f"Sprzedaż sztukowa top produktów per kasjer ({wybrany_miesiac})",
                        text_auto=".2s"
                    )

                    transakcje_df = df_top.groupby("Kasjer")["#"].nunique().reset_index().rename(
                        columns={"#": "Transakcje"})
                    sztuki_df = sztuki_df.merge(transakcje_df, on="Kasjer", how="left")
                    sztuki_df["Sztuki na transakcję"] = sztuki_df["Ilość"] / sztuki_df["Transakcje"]

                    fig_top2 = px.bar(
                        sztuki_df,
                        x="Kasjer",
                        y="Sztuki na transakcję",
                        color="PLU_nazwa",
                        title=f"Średnia liczba sprzedanych top produktów na transakcję ({wybrany_miesiac})",
                        text_auto=".2f"
                    )
                else:
                    fig_top1 = None
                    fig_top2 = None
            except Exception as e:
                print(f"Błąd przy wczytywaniu top produktów: {e}")
                fig_top1 = None
                fig_top2 = None

            df_loyal = dff[dff["Karta lojalnościowa"].str.upper() == "TAK"].copy()
            df_all = dff.copy()

            df_loyal["Kasjer"] = df_loyal["Stacja"].astype(str) + " - " + df_loyal["Login POS"].astype(str)
            df_all["Kasjer"] = df_all["Stacja"].astype(str) + " - " + df_all["Login POS"].astype(str)

            loyal_tx = df_loyal.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Lojalnościowe"})
            all_tx = df_all.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Wszystkie"})

            penetracja_df = pd.merge(all_tx, loyal_tx, on="Kasjer", how="left").fillna(0)
            penetracja_df["Penetracja"] = (penetracja_df["Lojalnościowe"] / penetracja_df["Wszystkie"]) * 100
            penetracja_df = penetracja_df.sort_values("Penetracja", ascending=False)

            fig_penetracja = px.bar(
                penetracja_df,
                x="Kasjer",
                y="Penetracja",
                title="Penetracja lojalnościowa per kasjer (%)",
                text_auto=".1f"
            )
            fig_penetracja.update_layout(yaxis_title="%", xaxis_title="Kasjer")

            content = [
                html.H3("Sprzedaż per kasjer"),
                html.H4("Ranking kasjerów wg obrotu netto"),
                dash_table.DataTable(
                    data=kasjer_summary.head(20).to_dict('records'),
                    columns=[{"name": col, "id": col} for col in kasjer_summary.columns],
                    style_table={'overflowX': 'auto'},
                    page_size=10
                ),
                dcc.Graph(className="custom-graph",figure=fig_kasjer),
                dcc.Graph(className="custom-graph",figure=fig_trans),
                dcc.Graph(className="custom-graph",figure=fig_avg),
                html.H4("Penetracja lojalnościowa per kasjer"),
                dcc.Graph(className="custom-graph",figure=fig_penetracja)
            ]

            if fig_top1 and fig_top2:
                content.extend([
                    html.H4("Analiza top produktów per kasjer"),
                    dcc.Graph(className="custom-graph",figure=fig_top1),
                    dcc.Graph(className="custom-graph",figure=fig_top2)
                ])

            return html.Div(content)

    # ---------------------------------------------
    # Callback dla heatmapy
    # ---------------------------------------------
    @app.callback(
        Output('heatmap-graph', 'figure'),
        Input('metric-selector', 'value'),
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('station-dropdown', 'value'),
        Input('group-dropdown', 'value')
    )
    def update_heatmap(metric, start_date, end_date, selected_stations, selected_groups):
        start_date_obj = pd.to_datetime(start_date).date()
        end_date_obj = pd.to_datetime(end_date).date()
        dff = df[(df["Data"] >= start_date_obj) &
                 (df["Data"] <= end_date_obj) &
                 (df["Stacja"].isin(selected_stations)) &
                 (df["Grupa towarowa"].isin(selected_groups))].copy()
        dff = dff[dff["Login POS"] != 99999].copy()

        dff["Godzina"] = pd.to_datetime(dff["Data_full"], errors="coerce").dt.hour
        dff["Dzień tygodnia"] = pd.to_datetime(dff["Data_full"], errors="coerce").dt.dayofweek

        dni = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
        godziny = list(range(24))
        full_index = pd.MultiIndex.from_product([range(7), godziny], names=["Dzień tygodnia", "Godzina"])

        if metric == "tx":
            grouped = dff.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
        elif metric == "netto":
            grouped = dff.groupby(["Dzień tygodnia", "Godzina"])["Netto"].sum()
        elif metric == "ilosc":
            grouped = dff.groupby(["Dzień tygodnia", "Godzina"])["Ilość"].sum()
        elif metric == "paliwo":
            grouped = dff[dff["HOIS"] == 0].groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
        elif metric == "lojalnosc":
            all_tx = dff.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique().rename("Wszystkie")
            loyal_tx = dff[dff["Karta lojalnościowa"].str.upper() == "TAK"].groupby(["Dzień tygodnia", "Godzina"])[
                "#"].nunique().rename("Lojalnościowe")
            merged = pd.merge(all_tx, loyal_tx, left_index=True, right_index=True, how="left").fillna(0)
            grouped = (merged["Lojalnościowe"] / merged["Wszystkie"] * 100).rename("Penetracja")
        else:
            grouped = pd.Series(dtype=float)

        grouped = grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")
        heat_pivot = grouped.pivot(index="Dzień tygodnia", columns="Godzina", values="Wartość")
        heat_pivot.index = [dni[i] for i in heat_pivot.index]

        fig = px.imshow(
            heat_pivot,
            labels=dict(x="Godzina", y="Dzień tygodnia", color=metric),
            x=[str(g) for g in godziny],
            aspect="auto",
            color_continuous_scale="Blues",
            title=f"📊 Heatmapa – {metric}"
        )

        fig.update_layout(
            xaxis_title="Godzina dnia",
            yaxis_title="Dzień tygodnia",
            yaxis=dict(autorange="reversed"),
            xaxis=dict(type="category", tickmode="linear")
        )

        return fig

    # ---------------------------------------------
    # Callback do usuwania wykresów z ulubionych
    # ---------------------------------------------
    @app.callback(
        Output('tabs-content', 'children', allow_duplicate=True),
        Input({'type': 'remove-favorite', 'index': dash.ALL}, 'n_clicks'),
        State('date-picker', 'start_date'),
        State('date-picker', 'end_date'),
        State('station-dropdown', 'value'),
        State('group-dropdown', 'value'),
        State('monthly-check', 'value'),
        prevent_initial_call=True
    )
    def remove_favorite(n_clicks, start_date, end_date, selected_stations, selected_groups, monthly_check):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks):
            return dash.no_update

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        fav_key = eval(button_id)['index']

        favorites = app.server.config.get('FAVORITES', set())
        if fav_key in favorites:
            favorites.remove(fav_key)
            app.server.config['FAVORITES'] = favorites

        return render_tab_content('tab6', start_date, end_date, selected_stations, selected_groups, monthly_check)

    @app.callback(
        Output("filter-panel", "className"),
        Output("filter-column", "width"),
        Output("content-column", "width"),
        Input("toggle-filter-button", "n_clicks"),
        State("filter-panel", "className"),
        prevent_initial_call=True
    )
    def toggle_filter_visibility(n_clicks, current_class):
        is_hidden = "hidden" in (current_class or "")
        new_class = "" if is_hidden else "hidden"
        return new_class, (3 if is_hidden else 0), (9 if is_hidden else 12)

    return app
