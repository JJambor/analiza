from random import random
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

import plotly.express as px
import plotly.io as pio
import holidays
import plotly.graph_objects as go

from main.core.dash_app import DashApp
from main.core.dash_layout import DashLayout
from main.enums.tabs import Tabs
from main.utils.utils_functions import get_free_days, format_metric_value


class Callbacks:
    app: DashApp = None
    dash_app: dash.Dash = None
    layout_app: DashLayout = None
    df_cached = None
    hois_cached = None
    def __init__(self, app: DashApp, layout: DashLayout ):
        self.app = app
        self.df_cached = app.get_df_cached()
        self.hois_cached = app.get_hois_cached()
        self.dash_app = app.get_dash_app()
        self.layout_app = layout

    def refresh(self, app: DashApp, layout: DashLayout):
        self.app = app
        self.df_cached = app.get_df_cached()
        self.hois_cached = app.get_hois_cached()
        self.dash_app = app.get_dash_app()
        self.layout_app = layout
    def register_callbacks(self):
        @self.dash_app.callback(
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
                    return self.app.get_station_options()
                elif button_id == 'deselect-all-stations':
                    return []
            return dash.no_update

        # ---------------------------------------------
        # Callback dla przycisków grup towarowych
        # ---------------------------------------------
        @self.dash_app.callback(
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
                    return self.app.get_group_options()
                elif button_id == 'deselect-all-groups':
                    return []
            return dash.no_update

        # Callback do aktualizacji listy produktów na podstawie wybranych grup towarowych
        @self.dash_app.callback(
            Output('product-dropdown', 'options'),
            Input('group-dropdown', 'value')
        )
        def update_product_options(selected_groups):
            if not selected_groups:
                return []

            df_filtered = self.df_cached[self.df_cached["Grupa towarowa"].isin(selected_groups)].copy()

            if df_filtered.empty:
                return []

            options = sorted(df_filtered["PLU_nazwa"].dropna().unique())

            return [{'label': opt, 'value': opt} for opt in options]

        # ---------------------------------------------
        # Callback renderujący zawartość zakładki
        # ---------------------------------------------
        @self.dash_app.callback(
            Output('tabs-content', 'children'),
            Input('tabs', 'value'),  # Fixed from 'value_1value' to 'value'
            Input('start-date', 'date'),
            Input('end-date', 'date'),

            Input('station-dropdown', 'value'),
            Input('group-dropdown', 'value'),
            Input('monthly-check', 'value'),
            Input('b2b-checklist', 'value'),
            Input('theme-store', 'data'),
            Input('product-dropdown', 'value')

        )
        def render_tab_content(tab, start_date, end_date, selected_stations, selected_groups, monthly_check, selected_b2b,
                               theme_data, selected_products):
            theme = theme_data.get("theme", "light")
            pio.templates.default = "corporate_dark" if theme == "dark" else "corporate_blue"
            start_date_obj = pd.to_datetime(start_date).date()
            end_date_obj = pd.to_datetime(end_date).date()

            # Filtrowanie danych
            dff = self.app.get_df()[
                (self.app.get_df()["Data"] >= start_date_obj) &
                (self.app.get_df()["Data"] <= end_date_obj) &
                (self.app.get_df()["Stacja"].isin(selected_stations)) &
                (self.app.get_df()["Grupa towarowa"].isin(selected_groups)) &
                (self.app.get_df()["B2B"].isin(selected_b2b))  # filtr B2B
                ].copy()
            if selected_products:
                dff = dff[dff["PLU_nazwa"].isin(selected_products)]

            # Usunięcie loginu technicznego
            dff = dff[dff["Login POS"] != 99999].copy()

            # Obsługa widoku miesięcznego
            if 'monthly' in monthly_check:
                dff["Okres"] = pd.to_datetime(dff["Data"]).dt.to_period("M").astype(str)
                category_col = "Stacja"
            else:
                dff["Okres"] = dff["Data"]
                category_col = None

            # Dalej możesz robić wykresy itp. na podstawie dff
            # return np. wykres, tabela lub komponent html

            if tab == Tabs.GENERAL.value:
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
                        fig_netto.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)
                        fig_tx.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)
                except Exception as e:
                    print("Błąd przy dodawaniu dni wolnych: ", e)

                return html.Div(children=[
                    html.H4("Ogólny"),

                    html.Div([
                        html.Div([
                            html.Div("Obrót netto (NFR+Fuel)", className="metric-label"),
                            html.Div(format_metric_value(total_netto, " zł"), className="metric-value")

                        ], className="metric-card"),

                        html.Div([
                            html.Div("Ilość transakcji", className="metric-label"),
                            html.Div(format_metric_value(total_transactions), className="metric-value")

                        ], className="metric-card"),

                        html.Div([
                            html.Div("Sprzedaż kawy", className="metric-label"),
                            html.Div(format_metric_value(kawa_netto, " zł"), className="metric-value")
                        ], className="metric-card"),

                        html.Div([
                            html.Div("Sprzedaż food", className="metric-label"),
                            html.Div(format_metric_value(food_netto, " zł"), className="metric-value")
                        ], className="metric-card"),

                        html.Div([
                            html.Div("Sprzedaż myjni", className="metric-label"),
                            html.Div(format_metric_value(myjnia_netto, " zł"), className="metric-value")
                        ], className="metric-card"),
                    ], className="metric-container"),

                    dcc.Graph(className="custom-graph", figure=fig_netto),
                    dcc.Graph(className="custom-graph", figure=fig_tx),

                    html.H4("Heatmapa"),
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
                    dcc.Graph(className="custom-graph", id='heatmap-graph')
                ])




            elif tab == Tabs.SHOP.value:

                netto_bez_hois0 = dff[dff["HOIS"] != 0]["Netto"].sum()

                unikalne_transakcje = dff["#"].nunique()

                avg_transaction = netto_bez_hois0 / unikalne_transakcje if unikalne_transakcje > 0 else 0

                netto_shop_df = dff[dff["HOIS"] != 0].groupby(["Okres"] + ([category_col] if category_col else []))[
                    "Netto"].sum().reset_index()

                fig_shop_netto = px.line(netto_shop_df, x="Okres", y="Netto", color=category_col,

                                         title="Obrót sklepowy netto (bez paliwa)", markers=True)

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
                        fig_shop_netto.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

                        fig_avg_tx.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

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

                                              title="Top 10 najlepiej sprzedających się produktów (bez paliwa)")

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
                            fig_station_avg.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

                    except:

                        pass

                content = [

                    html.H4("Sklep"),

                    html.Div([
                        html.Div([
                            html.Div("Obrót sklepowy netto", className="metric-label"),
                            html.Div(format_metric_value(netto_bez_hois0, " zł"), className="metric-value")

                        ], className="metric-card"),

                        html.Div([
                            html.Div("Średnia wartość transakcji", className="metric-label"),
                            html.Div(format_metric_value(avg_transaction, " zł"), className="metric-value")

                        ], className="metric-card"),
                    ], className="metric-container"),

                    dcc.Graph(className="custom-graph", figure=fig_shop_netto),

                    dcc.Graph(className="custom-graph", figure=fig_avg_tx),
                ]

                if fig_station_avg:
                    content.append(dcc.Graph(className="custom-graph", figure=fig_station_avg))

                if fig_top_products:

                    content.append(dcc.Graph(className="custom-graph", figure=fig_top_products))

                else:

                    content.append(html.Div("Brak danych do wygenerowania wykresu TOP 10.",

                                            style={'color': 'gray', 'fontStyle': 'italic'}))

                import plotly.graph_objects as go

                pareto_df = df_nonzero_hois[

                    ~df_nonzero_hois["Nazwa produktu"].str.lower().str.strip().isin(excluded_products)

                ].copy()

                pareto_df = pareto_df.groupby("Nazwa produktu")["Netto"].sum().reset_index()

                pareto_df = pareto_df.sort_values(by="Netto", ascending=False).head(30)

                pareto_df["Kumulacja"] = pareto_df["Netto"].cumsum() / pareto_df["Netto"].sum() * 100

                pareto_cutoff = pareto_df[pareto_df["Kumulacja"] <= 80].shape[0]

                pareto_df["Kolor"] = ["#0F4C81" if i < pareto_cutoff else "#B0BEC5" for i in range(len(pareto_df))]

                fig_pareto = go.Figure()

                fig_pareto.add_bar(

                    x=pareto_df["Nazwa produktu"],

                    y=pareto_df["Netto"],

                    marker_color=pareto_df["Kolor"],

                    name="Sprzedaż (netto)",

                    yaxis="y1",

                    hovertemplate='Produkt: %{x}<br>Netto: %{y:.2f} zł'

                )

                fig_pareto.add_trace(go.Scatter(

                    x=pareto_df["Nazwa produktu"],

                    y=pareto_df["Kumulacja"],

                    name="Kumulacja (%)",

                    yaxis="y2",

                    mode="lines+markers",

                    hovertemplate='Produkt: %{x}<br>Kumulacja: %{y:.2f}%'

                ))

                # Dopasowanie koloru tekstu do trybu
                text_color = "#000000" if theme != "dark" else "gray"

                if pareto_cutoff < len(pareto_df):
                    content.append(html.Div(
                        f"Granica 80% kumulacji: {pareto_df['Nazwa produktu'].iloc[pareto_cutoff]}",
                        style={
                            "color": text_color,
                            "fontWeight": "bold",
                            "marginBottom": "10px"
                        }
                    ))
                fig_pareto.update_layout(

                    title="Wykres Pareto produktów (bez HOIS 0, wg wartości netto)",

                    xaxis=dict(title="Nazwa produktu", tickangle=45, tickfont=dict(size=10)),

                    yaxis=dict(title="Netto (zł)", side="left"),

                    yaxis2=dict(title="Kumulacja (%)", overlaying="y", side="right", range=[0, 110]),

                    legend=dict(x=0.85, y=1.15),

                    margin=dict(t=80)

                )

                content.append(dcc.Graph(className="custom-graph", figure=fig_pareto))

                return html.Div(content)


            elif tab == Tabs.OIL.value:
                df_all = self.df_cached.copy()

                # Dodaj brakujące kolumny
                df_all["Grupa towarowa"] = df_all["HOIS"].map(lambda x: self.hois_cached.get(x, ("Nieznana", "Nieznana"))[0])
                df_all["Grupa sklepowa"] = df_all["HOIS"].map(lambda x: self.hois_cached.get(x, ("Nieznana", "Nieznana"))[1])

                # Dodaj "Okres"
                if 'monthly' in monthly_check:
                    df_all["Okres"] = pd.to_datetime(df_all["Data"]).dt.to_period("M").astype(str)
                    category_col = "Stacja"
                else:
                    df_all["Okres"] = df_all["Data"]
                    category_col = None

                # Filtrowanie tylko PALIWO
                fuel_df = df_all[
                    (df_all["Data"] >= start_date_obj) &
                    (df_all["Data"] <= end_date_obj) &
                    (df_all["Stacja"].isin(selected_stations)) &
                    (df_all["Grupa towarowa"].isin(selected_groups)) &
                    (df_all["Grupa sklepowa"] == "PALIWO") &
                    (df_all["B2B"].isin(selected_b2b)) &
                    (df_all["Login POS"] != 99999)
                    ].copy()

                if fuel_df.empty:
                    return html.Div(children=[
                        html.H3("Sprzedaż paliwa"),
                        html.P("Brak danych paliwowych dla wybranych filtrów.")
                    ])

                # METRYKI
                fuel_liters = fuel_df["Ilość"].sum()
                fuel_tx = fuel_df["#"].nunique()
                avg_liters_per_tx = fuel_liters / fuel_tx if fuel_tx != 0 else 0

                # Oblicz penetrację V-Power
                vpower_keywords = ["V-POWER", "VPOWER"]
                vpower_df = fuel_df[fuel_df["Nazwa produktu"].str.upper().str.contains("|".join(vpower_keywords))]
                vpower_liters = vpower_df["Ilość"].sum()

                # Odfiltruj AdBlue
                non_adblue_df = fuel_df[~fuel_df["Nazwa produktu"].str.upper().str.contains("ADBLUE")]
                non_adblue_liters = non_adblue_df["Ilość"].sum()

                penetracja_vpower = (vpower_liters / non_adblue_liters * 100) if non_adblue_liters else 0

                metrics = html.Div(className="metric-container", children=[
                    self.layout_app.generate_metric_card("Ilość litrów", format_metric_value(fuel_liters, " l")),
                    self.layout_app.generate_metric_card("Liczba transakcji paliwowych", format_metric_value(fuel_tx)),
                    self.layout_app.generate_metric_card("Penetracja V-Power", f"{penetracja_vpower:.1f}%"),
                    self.layout_app.generate_metric_card("Śr. litry / transakcja", f"{avg_liters_per_tx:.2f} l"),
                ])

                # Wykres sprzedaży paliwa
                fuel_sales_grouped = fuel_df.groupby(["Okres"] + ([category_col] if category_col else []))[
                    "Ilość"].sum().reset_index()
                fig_fuel_sales = px.line(fuel_sales_grouped, x="Okres", y="Ilość", color=category_col,
                                         title="Sprzedaż paliw", markers=True)

                # Potencjał flotowy
                non_b2b_invoice = fuel_df[(fuel_df["B2B"] != "TAK") & (fuel_df["Dokument"].str.upper() == "FAKTURA")]
                flota_data = pd.DataFrame({
                    "Typ": ["Potencjalni klienci flotowi", "Pozostali klienci"],
                    "Liczba": [len(non_b2b_invoice), len(fuel_df) - len(non_b2b_invoice)]
                })
                fig_flota = px.pie(flota_data, names="Typ", values="Liczba",
                                   title="Potencjał B2B", hole=0.4)
                fig_flota.update_traces(textposition='inside', textinfo='percent+label')

                # Analiza transakcji: paliwo vs paliwo + sklep
                all_tx = df_all[
                    (df_all["Data"] >= start_date_obj) &
                    (df_all["Data"] <= end_date_obj) &
                    (df_all["Stacja"].isin(selected_stations)) &
                    (df_all["Grupa towarowa"].isin(selected_groups)) &
                    (df_all["Login POS"] != 99999)
                    ][["#", "HOIS"]].copy()

                tx_agg = all_tx.groupby("#")["HOIS"].agg(['min', 'max']).reset_index()
                tx_agg["Typ"] = tx_agg.apply(
                    lambda row: "Tylko paliwo" if row["min"] == 0 and row["max"] == 0 else "Paliwo + sklep", axis=1)
                tx_summary = tx_agg["Typ"].value_counts().reset_index()
                tx_summary.columns = ["Typ", "Liczba"]

                fig_mix = px.pie(tx_summary, names="Typ", values="Liczba",
                                 title="Tylko paliwo vs paliwo + sklep", hole=0.4)
                fig_mix.update_traces(textposition='inside', textinfo='percent+label')

                # B2B / B2C
                fuel_df["Typ klienta"] = fuel_df["B2B"].apply(lambda x: "B2B" if str(x).upper() == "TAK" else "B2C")
                customer_types = fuel_df.groupby("Typ klienta")["Ilość"].sum().reset_index()
                fig_customer_types = px.pie(customer_types, values="Ilość", names="Typ klienta",
                                            title="Stosunek tankowań B2C do B2B", hole=0.4)
                fig_customer_types.update_traces(textposition='inside', textinfo='percent+label')

                # Udział produktów paliwowych
                fuel_sales = fuel_df.groupby("Nazwa produktu")["Ilość"].sum().nlargest(10).reset_index()
                fig_fuel_products = px.pie(fuel_sales, names="Nazwa produktu", values="Ilość",
                                           title="Udział paliw", hole=0.4)

                # Dni wolne
                try:
                    start_dt = pd.to_datetime(fuel_df["Okres"].min())
                    end_dt = pd.to_datetime(fuel_df["Okres"].max())
                    free_days = get_free_days(start_dt, end_dt)
                    for day in free_days:
                        fig_fuel_sales.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)
                except Exception as e:
                    print("Błąd przy dodawaniu dni wolnych: ", e)

                return html.Div(children=[
                    html.H4("Paliwo"),
                    metrics,

                    html.H4("Sprzedaż paliw"),
                    dbc.Row([
                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_fuel_sales), width=12)
                    ]),

                    dbc.Row([
                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_flota), xs=12, md=6),
                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_mix), xs=12, md=6)
                    ], className="graph-row"),

                    dbc.Row([
                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_customer_types), xs=12, md=6),
                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_fuel_products), xs=12, md=6)
                    ], className="graph-row")
                ])




            elif tab == Tabs.LOYALITY.value:
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

                df_prev_filtered = self.app.get_df()[
                    (self.app.get_df()["Data"] >= start_date_prev.date()) &
                    (self.app.get_df()["Data"] <= end_date_prev.date())
                    ].copy()

                df_prev_filtered["Grupa towarowa"] = df_prev_filtered["HOIS"].map(
                    lambda x: self.app.get_hois_map().get(x, ("Nieznana", "Nieznana"))[0])
                df_prev_filtered["Grupa sklepowa"] = df_prev_filtered["HOIS"].map(
                    lambda x: self.app.get_hois_map().get(x, ("Nieznana", "Nieznana"))[1])

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
                    fig_pen.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

                fig_loyal = px.line(loyal_daily, x="Okres", y="Lojalnościowe", title="Transakcje lojalnościowe")
                fig_loyal.update_traces(mode="lines+markers")
                fig_loyal.update_layout(xaxis_tickformat="%d.%m")
                for day in free_days:
                    fig_loyal.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

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
                    fig_combined.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

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
                    html.H4("Lojalność"),
                    html.Div([
                        html.Div([
                            html.Div("Średnia penetracja (obecny zakres)", className="metric-label"),
                            html.Div(f"{penetration_current:.2f}%", className="metric-value"),
                            html.Div(f"Zmiana: {delta_value:.2f}%", className=f"metric-delta " +
                                                                              (
                                                                                  "positive" if delta_value > 0 else "negative" if delta_value < 0 else "neutral"))
                        ], className="metric-card"),

                        html.Div([
                            html.Div(f"Średnia penetracja ({prev_label})", className="metric-label"),
                            html.Div(f"{penetration_prev:.2f}%", className="metric-value")
                        ], className="metric-card"),
                    ], className="metric-container"),

                    dcc.Graph(className="custom-graph", figure=fig_pen),
                    dcc.Graph(className="custom-graph", figure=fig_loyal),
                    dcc.Graph(className="custom-graph", figure=fig_combined),
                    html.Div([
                        html.Div([
                            html.H6("TOP / BOTTOM 5 grup towarowych wg penetracji lojalnościowej"),
                            dbc.Row([
                                dbc.Col([
                                    html.Div("TOP 5", className="loyalty-table-title"),
                                    html.Div(
                                        dash_table.DataTable(
                                            data=merged_top.head(5).rename(columns={"Grupa towarowa": "Grupa"}).to_dict(
                                                'records'),
                                            columns=[
                                                {"name": "Grupa", "id": "Grupa"},
                                                {"name": "Penetracja (%)", "id": "Penetracja", "type": "numeric",
                                                 "format": {"specifier": ".2f"}}
                                            ],
                                            style_cell={
                                                'fontFamily': 'Open Sans, sans-serif',
                                                'fontSize': '14px',
                                                'padding': '10px',
                                                'border': 'none'
                                            },
                                            style_data_conditional=[
                                                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'},
                                            ],
                                            style_header={
                                                'backgroundColor': '#f1f7ff',
                                                'fontWeight': 'bold',
                                                'borderBottom': '2px solid #e3e7ec'
                                            },
                                            style_table={
                                                'overflowX': 'auto',
                                                'borderRadius': '6px'
                                            },
                                            style_as_list_view=True
                                        ),
                                        className="loyalty-datatable"
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Div("BOTTOM 5", className="loyalty-table-title"),
                                    html.Div(
                                        dash_table.DataTable(
                                            data=merged_top.tail(5).rename(columns={"Grupa towarowa": "Grupa"}).to_dict(
                                                'records'),
                                            columns=[
                                                {"name": "Grupa", "id": "Grupa"},
                                                {"name": "Penetracja (%)", "id": "Penetracja", "type": "numeric",
                                                 "format": {"specifier": ".2f"}}
                                            ],
                                            style_cell={
                                                'fontFamily': 'Open Sans, sans-serif',
                                                'fontSize': '14px',
                                                'padding': '10px',
                                                'border': 'none'
                                            },
                                            style_data_conditional=[
                                                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'},
                                            ],
                                            style_header={
                                                'backgroundColor': '#f1f7ff',
                                                'fontWeight': 'bold',
                                                'borderBottom': '2px solid #e3e7ec'
                                            },
                                            style_table={
                                                'overflowX': 'auto',
                                                'borderRadius': '6px'
                                            },
                                            style_as_list_view=True
                                        ),
                                        className="loyalty-datatable"
                                    )
                                ], width=6)
                            ], className="loyalty-table-container")
                        ])

                    ])])




            elif tab == Tabs.WASH.value:

                carwash_df = dff[dff["Grupa sklepowa"] == "MYJNIA INNE"]

                if carwash_df.empty:
                    return html.Div(children=[

                        html.H3("Myjnia"),

                        html.P("Brak danych myjni dla wybranych filtrów.")

                    ])

                # METRYKI MYJNI (ilość sztuk zamiast zł)

                sales_total = carwash_df["Ilość"].sum()

                sales_karnet = carwash_df[carwash_df["Nazwa produktu"].str.lower().str.startswith("karnet")]["Ilość"].sum()

                def classify_program_all(nazwa):

                    nazwa = nazwa.lower()

                    if "standard" in nazwa:

                        return "Myjnia Standard"

                    elif "express" in nazwa:

                        return "Myjnia Express"

                    else:

                        return "Pozostałe"

                carwash_df["Program"] = carwash_df["Nazwa produktu"].apply(classify_program_all)

                program_sales = carwash_df.groupby("Program")["Ilość"].sum().to_dict()

                carwash_df["Typ produktu"] = carwash_df["Nazwa produktu"].str.lower().apply(

                    lambda x: "Karnet" if x.startswith("karnet") else "Inne"

                )

                all_tx = dff["#"].nunique()

                carwash_tx = carwash_df["#"].nunique()

                penetration = (carwash_tx / all_tx) * 100 if all_tx else 0

                metric_carwash = html.Div(className="metric-container", children=[
                    self.layout_app.generate_metric_card("Sprzedane programy", format_metric_value(sales_total, " szt.")),
                    self.layout_app.generate_metric_card("Udział myjnii", f"{penetration:.1f}%"),
                    self.layout_app.generate_metric_card("Karnety", format_metric_value(sales_karnet, " szt.")),
                    self.layout_app.generate_metric_card("Standard", format_metric_value(program_sales.get('Myjnia Standard', 0), " szt.")),
                    self.layout_app.generate_metric_card("Express", format_metric_value(program_sales.get('Myjnia Express', 0), " szt."))
                ])

                carwash_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[

                    "Ilość"].sum().reset_index()

                fig_carwash = px.line(carwash_grouped, x="Okres", y="Ilość", color=category_col,

                                      title="Sprzedaż usług myjni", markers=True)

                sales_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[

                    "Netto"].sum().reset_index()

                fig_sales = px.line(sales_grouped, x="Okres", y="Netto", color=category_col,

                                    title="Sprzedaż netto grupy Myjnia", markers=True)

                pie_df = carwash_df.groupby("Typ produktu")["Ilość"].sum().reset_index()

                fig_karnet = px.pie(pie_df, values="Ilość", names="Typ produktu",

                                    title="Udział karnetów w sprzedaży MYJNIA INNE", hole=0.4)

                fig_karnet.update_traces(textposition='inside', textinfo='percent+label')

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
                        fig_carwash.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

                        fig_sales.add_vline(x=day, line_dash="dot", line_color="orange", opacity=0.2)

                except Exception as e:

                    print("Błąd przy dodawaniu dni wolnych: ", e)

                return html.Div(children=[

                    html.H4("Myjnia"),

                    metric_carwash,

                    dbc.Row(children=[

                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_carwash), width=12)

                    ]),

                    dbc.Row(children=[

                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_sales), width=12)

                    ]),

                    dbc.Row(children=[

                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_karnet), width=6),

                        dbc.Col(dcc.Graph(className="custom-graph", figure=fig_program_all), width=6)

                    ])

                ])



            elif tab == Tabs.FAVORITES.value:
                favorites = self.dash_app.server.config.get('FAVORITES', set())
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
                            dcc.Graph(className="custom-graph", figure=fig),
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

            elif tab == Tabs.SELL_PER_CASHIER.value:
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
                # Sekcja layout
                content = [
                    html.H4("Sprzedaż per kasjer"),
                    html.Div([
                        html.H6("Ranking kasjerów wg obrotu netto"),
                        dbc.Row([
                            dbc.Col([
                                html.Div(
                                    dash_table.DataTable(
                                        data=kasjer_summary.head(10).to_dict('records'),
                                        columns=[{"name": col, "id": col} for col in kasjer_summary.columns],
                                        style_cell={
                                            'fontFamily': 'Open Sans, sans-serif',
                                            'fontSize': '14px',
                                            'padding': '10px',
                                            'border': 'none'
                                        },
                                        style_data_conditional=[
                                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'},
                                        ],
                                        style_header={
                                            'backgroundColor': '#f1f7ff',
                                            'fontWeight': 'bold',
                                            'borderBottom': '2px solid #e3e7ec'
                                        },
                                        style_table={
                                            'overflowX': 'auto',
                                            'borderRadius': '6px'
                                        },
                                        style_as_list_view=True,
                                        page_size=10
                                    ),
                                    className="loyalty-datatable"
                                )
                            ], width=12)
                        ], className="loyalty-table-container")
                    ]),
                    dcc.Graph(className="custom-graph", figure=fig_kasjer),
                    dcc.Graph(className="custom-graph", figure=fig_trans),
                    dcc.Graph(className="custom-graph", figure=fig_avg),
                    html.H4("Penetracja lojalnościowa per kasjer"),
                    dcc.Graph(className="custom-graph", figure=fig_penetracja),
                ]
                # Dropdown + placeholder pod dynamiczne wykresy top produktów
                try:
                    top_products_df = pd.read_csv("top_products.csv", sep=";")
                    top_products_df["MIESIĄC"] = top_products_df["MIESIĄC"].astype(str)

                    dropdown_top_month = dcc.Dropdown(
                        id="top-month-dropdown",
                        options=[{"label": m, "value": m} for m in sorted(top_products_df["MIESIĄC"].unique())],
                        value=sorted(top_products_df["MIESIĄC"].unique())[-1],
                        clearable=False,
                        className="mb-4"
                    )

                    content.extend([
                        html.H6("Analiza top produktów per kasjer"),
                        html.Div([
                            html.Label("Wybierz miesiąc:"),
                            dropdown_top_month
                        ]),
                        dcc.Graph(id="top-products-graph", className="custom-graph"),
                        dcc.Graph(id="top-products-per-tx-graph", className="custom-graph")
                    ])
                except Exception as e:
                    print(f"Błąd przy wczytywaniu dropdowna miesiąca: {e}")

                return html.Div(content)
            # CALLBACK DO DROPDOWN TOP PRODUKTY

        @self.dash_app.callback(
            Output("top-products-graph", "figure"),
            Output("top-products-per-tx-graph", "figure"),
            Input("top-month-dropdown", "value"),
            Input('start-date', 'date'),
            Input('end-date', 'date'),

            State('station-dropdown', 'value'),
            State('group-dropdown', 'value'),
            Input("theme-store", "data")
        )
        def update_top_products_graphs(selected_month, start_date, end_date, selected_stations, selected_groups,
                                       theme_data):
            theme = theme_data.get("theme", "light")
            pio.templates.default = "corporate_dark" if theme == "dark" else "corporate_blue"
            try:
                # Szybko: użycie cache zamiast ponownego wczytywania
                df_all = self.df_cached.copy()
                hois_map = self.hois_cached.copy()

                df_all["Grupa towarowa"] = df_all["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[0])
                df_all["Data"] = pd.to_datetime(df_all["Data"])
                df_all = df_all[df_all["Login POS"] != 99999]

                # Filtrowanie na podstawie zakresu dat, stacji i grup
                df_filtered = df_all[
                    (df_all["Data"] >= pd.to_datetime(start_date)) &
                    (df_all["Data"] <= pd.to_datetime(end_date)) &
                    (df_all["Stacja"].isin(selected_stations)) &
                    (df_all["Grupa towarowa"].isin(selected_groups))
                    ].copy()

                # Przygotowanie danych
                df_filtered["Kasjer"] = df_filtered["Stacja"].astype(str) + " - " + df_filtered["Login POS"].astype(str)
                df_filtered["Miesiąc"] = df_filtered["Data"].dt.to_period("M").astype(str)
                df_filtered["PLU"] = df_filtered["PLU"].astype(str).str.strip()

                # Top produkty z pliku CSV
                top_products_df = pd.read_csv("top_products.csv", sep=";")
                top_products_df["MIESIĄC"] = top_products_df["MIESIĄC"].astype(str)
                top_products_df["PLU"] = top_products_df["PLU"].astype(str).str.strip()
                nazwy_plu = top_products_df.set_index("PLU")["NAZWA"].to_dict()

                top_plu_list = top_products_df[top_products_df["MIESIĄC"] == selected_month]["PLU"].tolist()

                # Filtrowanie danych sprzedażowych do top PLU i wybranego miesiąca
                df_top = df_filtered[
                    (df_filtered["Miesiąc"] == selected_month) &
                    (df_filtered["PLU"].isin(top_plu_list))
                    ].copy()

                if df_top.empty:
                    return go.Figure(), go.Figure()

                df_top["PLU_nazwa"] = df_top["PLU"].map(nazwy_plu)

                # ➕ Ograniczenie do top 20 kasjerów (by uniknąć lagów)
                top_kasjerzy = df_top.groupby("Kasjer")["Ilość"].sum().nlargest(20).index.tolist()
                df_top = df_top[df_top["Kasjer"].isin(top_kasjerzy)]

                # Wykres 1: liczba sprzedanych sztuk per kasjer i produkt
                sztuki_df = df_top.groupby(["Kasjer", "PLU_nazwa"])["Ilość"].sum().reset_index()

                fig1 = px.bar(
                    sztuki_df,
                    x="Kasjer",
                    y="Ilość",
                    color="PLU_nazwa",
                    title=f"Sprzedaż sztukowa top produktów ({selected_month})",
                    text_auto=".2s"
                )
                fig1.update_layout(barmode="stack", xaxis_tickangle=-45)

                # Wykres 2: średnia liczba sztuk na transakcję
                transakcje_df = df_top.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Transakcje"})
                sztuki_df = sztuki_df.merge(transakcje_df, on="Kasjer", how="left")
                sztuki_df["Sztuki na transakcję"] = sztuki_df["Ilość"] / sztuki_df["Transakcje"]

                fig2 = px.bar(
                    sztuki_df,
                    x="Kasjer",
                    y="Sztuki na transakcję",
                    color="PLU_nazwa",
                    title=f"Średnia liczba sprzedanych top produktów na transakcję ({selected_month})",
                    text_auto=".2f"
                )
                fig2.update_layout(barmode="stack", xaxis_tickangle=-45)

                return fig1, fig2

            except Exception as e:
                print(f"Błąd w callbacku top produktów: {e}")
                return go.Figure(), go.Figure()

        # ---------------------------------------------
        # Callback dla heatmapy
        # ---------------------------------------------
        @self.dash_app.callback(
            Output('heatmap-graph', 'figure'),
            Input('metric-selector', 'value'),
            Input('start-date', 'date'),
            Input('end-date', 'date'),

            Input('station-dropdown', 'value'),
            Input('group-dropdown', 'value'),
            Input("theme-store", "data"),
            Input('product-dropdown', 'value'),
            Input('b2b-checklist', 'value')

        )
        def update_heatmap(metric, start_date, end_date, selected_stations, selected_groups, theme_data, selected_products,
                           selected_b2b):
            theme = theme_data.get("theme", "light")
            pio.templates.default = "corporate_dark" if theme == "dark" else "corporate_blue"
            start_date_obj = pd.to_datetime(start_date).date()
            end_date_obj = pd.to_datetime(end_date).date()
            dff = self.app.get_df()[(self.app.get_df()["Data"] >= start_date_obj) &
                     (self.app.get_df()["Data"] <= end_date_obj) &
                     (self.app.get_df()["Stacja"].isin(selected_stations)) &
                     (self.app.get_df()["B2B"].isin(selected_b2b)) &
                     (self.app.get_df()["Grupa towarowa"].isin(selected_groups))].copy()

            dff = dff[dff["Login POS"] != 99999].copy()
            if selected_products:
                dff = dff[dff["PLU_nazwa"].isin(selected_products)]

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

            color_scale = "Blues" if theme != "dark" else "Blues_r"

            fig = px.imshow(
                heat_pivot,
                labels=dict(x="Godzina", y="Dzień tygodnia", color=metric),
                x=[str(g) for g in godziny],
                aspect="auto",
                color_continuous_scale=color_scale,
                title=f"📊 Heatmapa – {metric}"
            )

            fig.update_layout(
                xaxis_title="Godzina",
                yaxis_title="Dzień tygodnia",
                yaxis=dict(autorange="reversed"),
                xaxis=dict(type="category", tickmode="linear")
            )

            return fig

        # ---------------------------------------------
        # Callback do usuwania wykresów z ulubionych
        # ---------------------------------------------
        @self.dash_app.callback(
            Output('tabs-content', 'children', allow_duplicate=True),
            Input({'type': 'remove-favorite', 'index': dash.ALL}, 'n_clicks'),
            Input('start-date', 'date'),
            Input('end-date', 'date'),

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

            favorites = self.dash_app.get_dash_app().server.config.get('FAVORITES', set())
            if fav_key in favorites:
                favorites.remove(fav_key)
                self.app.server.config['FAVORITES'] = favorites

            return render_tab_content('tab6', start_date, end_date, selected_stations, selected_groups, monthly_check)

        @self.dash_app.callback(
            Output("filter-panel", "className"),
            Output("filter-column", "className"),
            Output("content-column", "className"),
            Output("trigger-graph-resize", "data"),
            Input("toggle-filter-button", "n_clicks"),
            State("filter-panel", "className"),
            prevent_initial_call=True
        )
        def toggle_filter_panel(n_clicks, current_class):
            filters_hidden = "hidden" in current_class

            if filters_hidden:
                return (
                    "",  # filtr znowu widoczny
                    "responsive-filter",
                    "responsive-content",  # normalna szerokość wykresów
                    {"value": random()}  # wyzwalacz dla clientside resize
                )
            else:
                return (
                    "hidden",  # chowamy panel
                    "responsive-filter hidden",
                    "responsive-content expanded",  # wykresy na całą szerokość
                    {"value": random()}  # wyzwalacz dla clientside resize
                )

        # przełączanie trybu jasny/ciemny
        @self.dash_app.callback(
            Output('theme-store', 'data'),
            Input('theme-toggle-button', 'n_clicks'),
            Input('theme-store', 'data'),
            prevent_initial_call=True
        )
        def toggle_theme(n, current_theme):
            new_theme = 'dark' if current_theme.get('theme') == 'light' else 'light'
            return {'theme': new_theme}

        self.dash_app.clientside_callback(
            """
            function(themeData) {
                if (!themeData || !themeData.theme) return window.dash_clientside.no_update;

                const theme = themeData.theme;
                const body = document.body;

                if (theme === 'dark') {
                    body.classList.add('dark');
                    return '☀️';
                } else {
                    body.classList.remove('dark');
                    return '🌙';
                }
            }
            """,
            Output("theme-toggle-button", "children"),
            Input("theme-store", "data"),
            prevent_initial_call=True
        )

        self.dash_app.clientside_callback(
            """
            function(trigger) {
                setTimeout(() => {
                    const graphs = document.querySelectorAll('.js-plotly-plot');
                    graphs.forEach(g => {
                        Plotly.Plots.resize(g);
                    });
                }, 300);
                return window.dash_clientside.no_update;
            }
            """,
            Output("theme-toggle-button", "n_clicks"),  # dummy output
            Input("trigger-graph-resize", "data")
        )
