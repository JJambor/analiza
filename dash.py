import streamlit as st
import pandas as pd
import plotly.express as px
import time
import uuid
import holidays
import networkx as nx
import plotly.graph_objects as go

st.set_page_config(layout="wide")


def get_free_days(start_date, end_date):
    pl_holidays = holidays.Poland(years=range(start_date.year, end_date.year + 1))
    date_range = pd.date_range(start=start_date, end=end_date)
    return [date for date in date_range if date.weekday() >= 5 or date in pl_holidays]


def style_plotly(fig, hovertemplate=None):
    # 🎨 Kolory
    custom_colors = px.colors.qualitative.Set2
    fig.update_layout(colorway=custom_colors)

    # 🕶️ Styl tła i czcionki
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=14),
        hovermode="x unified"
    )

    # 🧠 Tooltip
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)

    return fig


@st.cache_data(ttl=3600, show_spinner="Ładowanie mapy HOIS...")
def load_hois_map():
    file_path = "hois_map.csv"
    hois_df = pd.read_csv(file_path, encoding="utf-8", sep=";")
    hois_df.columns = [col.strip() for col in hois_df.columns]

    expected_columns = ["HOIS", "Grupa towarowa", "Grupa sklepowa"]
    actual_columns = hois_df.columns.tolist()

    if len(actual_columns) != len(expected_columns):
        st.error(f"Plik CSV powinien mieć kolumny: {expected_columns}, ale znaleziono: {actual_columns}")
        return {}

    return {row["HOIS"]: (row["Grupa towarowa"], row["Grupa sklepowa"]) for _, row in hois_df.iterrows()}


hois_map = load_hois_map()


@st.cache_data(ttl=3600, show_spinner="Ładowanie danych sprzedażowych...")
def load_data():
    files = ["data01.xlsx", "data02.xlsx", "data03.xlsx"]
    dfs = []

    for file in files:
        try:
            df_month = pd.read_excel(file)

            if "Data" not in df_month.columns:
                st.error(f"W pliku {file} brak kolumny 'Data'")
                continue

            # Zamiana na datetime z godziną
            df_month["Data_full"] = pd.to_datetime(df_month["Data"], errors="coerce", format=None)

            null_dates = df_month["Data_full"].isnull().sum()
            if null_dates > 0:
                st.warning(f"W pliku {file} znaleziono {null_dates} pustych lub błędnych dat.")

            # Dodatkowa kolumna tylko z datą (bez godziny) – do filtrowania
            df_month["Data"] = df_month["Data_full"].dt.date

            dfs.append(df_month)

            with st.container():
                placeholder = st.empty()
                placeholder.markdown(f"""
                    <div style='margin-top: 30px;'>
                        <p style='color: green; font-weight: bold;'>Wczytano poprawnie {file}, {len(df_month)} wierszy.</p>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(3)
                placeholder.empty()

        except Exception as e:
            st.error(f"Błąd przy wczytywaniu {file}: {e}")

    if len(dfs) == 0:
        st.error("Brak poprawnych danych do połączenia!")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(subset=["Data_full"])

    return df


df = load_data()

if df.empty or df["Data"].isnull().all():
    st.error("Dane są puste lub wszystkie daty są niepoprawne!")
    st.stop()

df["Grupa towarowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[0])
df["Grupa sklepowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[1])

st.sidebar.header("Filtry")
start_date = st.sidebar.date_input("Od", df["Data"].min())
end_date = st.sidebar.date_input("Do", df["Data"].max())

station_options = df["Stacja"].unique()
select_all_stations = st.sidebar.checkbox("Zaznacz wszystkie stacje", value=True)
selected_stations = station_options.tolist() if select_all_stations else st.sidebar.multiselect("Wybierz stacje",
                                                                                                station_options,
                                                                                                default=station_options)

group_options = df["Grupa towarowa"].unique()
select_all_groups = st.sidebar.checkbox("Zaznacz wszystkie grupy towarowe", value=True)
selected_groups = group_options.tolist() if select_all_groups else st.sidebar.multiselect("Wybierz grupy towarowe",
                                                                                          group_options,
                                                                                          default=group_options)

df_filtered = df[(df["Data"] >= start_date) & (df["Data"] <= end_date) & (df["Stacja"].isin(selected_stations)) & (
    df["Grupa towarowa"].isin(selected_groups))].copy()
df_filtered = df_filtered[df_filtered["Login POS"] != 99999].copy()

if df_filtered.empty:
    st.warning("Brak danych po zastosowaniu wybranych filtrów!")
    st.stop()

monthly_station_view = st.sidebar.checkbox("Widok miesięczny według stacji", value=False)
df_filtered["Okres"] = pd.to_datetime(df_filtered["Data"]).dt.to_period("M").astype(str) if monthly_station_view else \
    df_filtered["Data"]
category_col = "Stacja" if monthly_station_view else None

# Dodaj zakładki, aby zdefiniować zmienną tab1 itd.
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Ogólny", "Sklep", "Paliwo", "Lojalność", "Myjnia", "Ulubione", "Sprzedaż per kasjer"])

if "favorite_charts" not in st.session_state:
    st.session_state.favorite_charts = set()
favorite_charts = st.session_state.favorite_charts


def plot_line_chart(df, x, y, color, title, key_suffix="", fill_area=False):
    fig = px.line(
        df, x=x, y=y, color=color, title=title, markers=True
    )

    line_mode = "lines+markers"
    line_shape = "spline"

    if fill_area:
        fig.update_traces(mode=line_mode, line_shape=line_shape, fill="tozeroy")
    else:
        fig.update_traces(mode=line_mode, line_shape=line_shape)

    try:
        start_date = pd.to_datetime(df[x].min())
        end_date = pd.to_datetime(df[x].max())
        free_days = get_free_days(start_date, end_date)
        for day in free_days:
            fig.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
    except Exception as e:
        st.warning(f"Błąd przy dodawaniu dni wolnych: {e}")

    hovertemplate = f"<b>{x}:</b> %{{x}}<br><b>{y}:</b> %{{y:.2f}}"
    fig = style_plotly(fig, hovertemplate)

    col_plot, col_fav = st.columns([0.9, 0.1])
    plot_key = f"{title}_{key_suffix}"
    with col_plot:
        st.plotly_chart(fig, use_container_width=True, key=plot_key)
    st.session_state[f"fig_{plot_key}"] = fig

    with col_fav:
        fav_key = f"{title}_{key_suffix}"
        fav_style = """
    <style>
    .fav-btn {
        background-color: transparent;
        color: white;
        border: 2px solid white;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 16px;
        cursor: pointer;
    }
    .fav-btn.active {
        background-color: white;
        color: black;
    }
    </style>
    """
    st.markdown(fav_style, unsafe_allow_html=True)

    fav_key = f"{title}_{key_suffix}"
    is_active = "active" if fav_key in st.session_state.favorite_charts else ""
    btn_html = f"<button class='fav-btn {is_active}'>★</button>"
    clicked = st.button("★", key=f"fav_btn_{fav_key}")
    if clicked:
        if fav_key not in st.session_state.favorite_charts:
            st.session_state.favorite_charts.add(fav_key)
            st.success(f"Dodano do ulubionych: {title}")


with tab1:
    st.header("Ogólny")
    total_netto = df_filtered["Netto"].sum()
    total_transactions = df_filtered["#"].nunique()

    # Nowe metryki
    kawa_netto = df_filtered[df_filtered["Grupa sklepowa"] == "NAPOJE GORĄCE"]["Netto"].sum()
    food_netto = \
        df_filtered[df_filtered["Grupa towarowa"].str.strip().str.upper().isin(["FOOD SERVICE", "USLUGI DODATKOWE"])][
            "Netto"].sum()
    myjnia_netto = df_filtered[df_filtered["Grupa sklepowa"] == "MYJNIA INNE"]["Netto"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Obrót netto(NFR+Fuel)", f"{total_netto / 1_000_000:.1f} mln zł")
    col2.metric("Unikalne transakcje", f"{total_transactions / 1000:,.0f} tys.")
    col3.metric("Sprzedaż kawy", f"{round(kawa_netto / 1000):,} tys. zł")
    col4.metric("Sprzedaż food", f"{round(food_netto / 1000):,} tys. zł")
    col5.metric("Sprzedaż myjni", f"{round(myjnia_netto / 1000):,} tys. zł")

    plot_line_chart(
        df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index(),
        "Okres", "Netto", category_col, "Obrót netto (NFR+Fuel)")
    plot_line_chart(
        df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index(),
        "Okres", "#", category_col, "Liczba transakcji")

    # HEAT MAPA

    st.subheader("Heatmapa transakcji – dzień tygodnia vs godzina")

    # 🧠 Wybór metryki
    selected_metric = st.radio(
        "Wybierz metrykę do analizy:",
        options=[
            "Liczba transakcji",
            "Obrót netto",
            "Liczba sztuk",
            "Transakcje paliwowe",
            "Penetracja lojalnościowa"
        ],
        horizontal=True
    )

    # Przygotowanie danych czasowych
    df_filtered["Godzina"] = pd.to_datetime(df_filtered["Data_full"], errors="coerce").dt.hour
    df_filtered["Dzień tygodnia"] = pd.to_datetime(df_filtered["Data_full"], errors="coerce").dt.dayofweek

    dni = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
    godziny = list(range(24))
    full_index = pd.MultiIndex.from_product([range(7), godziny], names=["Dzień tygodnia", "Godzina"])

    # 📊 Wyliczanie metryki
    if selected_metric == "Liczba transakcji":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
        df_grouped = df_grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")

    elif selected_metric == "Obrót netto":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["Netto"].sum()
        df_grouped = df_grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")

    elif selected_metric == "Liczba sztuk":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["Ilość"].sum()
        df_grouped = df_grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")

    elif selected_metric == "Transakcje paliwowe":
        paliwo_df = df_filtered[df_filtered["HOIS"] == 0]
        df_grouped = paliwo_df.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
        df_grouped = df_grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")

    elif selected_metric == "Penetracja lojalnościowa":
        # Wszystkie transakcje
        all_tx = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique().rename("Wszystkie")
        # Z kartą
        loyal_tx = \
        df_filtered[df_filtered["Karta lojalnościowa"].str.upper() == "TAK"].groupby(["Dzień tygodnia", "Godzina"])[
            "#"].nunique().rename("Lojalnościowe")

        merged = pd.merge(all_tx, loyal_tx, left_index=True, right_index=True, how="left").fillna(0)
        merged["Penetracja"] = (merged["Lojalnościowe"] / merged["Wszystkie"]) * 100
        df_grouped = merged["Penetracja"].reindex(full_index, fill_value=0).reset_index(name="Wartość")

    # 🔁 Pivot + konwersja osi
    heat_pivot = df_grouped.pivot(index="Dzień tygodnia", columns="Godzina", values="Wartość")
    heat_pivot.index = [dni[i] for i in heat_pivot.index]

    # 🎨 Heatmapa
    fig_heatmap = px.imshow(
        heat_pivot,
        labels=dict(x="Godzina", y="Dzień tygodnia", color=selected_metric),
        x=[str(g) for g in godziny],
        aspect="auto",
        color_continuous_scale="Blues",
        title=f"📊 Heatmapa – {selected_metric}"
    )

    fig_heatmap.update_layout(
        xaxis_title="Godzina dnia",
        yaxis_title="Dzień tygodnia",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(type="category", tickmode="linear")
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)
with tab2:
    st.header("Sklep")

    netto_bez_hois0 = df_filtered[df_filtered["HOIS"] != 0]["Netto"].sum()
    unikalne_transakcje = df_filtered["#"].nunique()
    avg_transaction = netto_bez_hois0 / unikalne_transakcje if unikalne_transakcje > 0 else 0

    st.metric("Średnia wartość transakcji (obrót bez HOIS 0 / wszystkie transakcje)", f"{avg_transaction:.2f} zł")

    # 🔄 Obrót sklepowy netto (bez HOIS 0)
    netto_shop_df = df_filtered[df_filtered["HOIS"] != 0].groupby(["Okres"] + ([category_col] if category_col else []))[
        "Netto"].sum().reset_index()
    plot_line_chart(netto_shop_df, "Okres", "Netto", category_col, "Obrót sklepowy netto (bez HOIS 0)",
                    key_suffix="sklep")

    netto_bez_hois0_mies = df_filtered[df_filtered["HOIS"] != 0].groupby("Okres")["Netto"].sum()
    transakcje_all_mies = df_filtered.groupby("Okres")["#"].nunique()

    avg_mies_df = pd.concat([netto_bez_hois0_mies, transakcje_all_mies], axis=1).reset_index()
    avg_mies_df.columns = ["Okres", "Netto_bez_HOIS0", "Transakcje_all"]
    avg_mies_df["Srednia"] = avg_mies_df["Netto_bez_HOIS0"] / avg_mies_df["Transakcje_all"]

    plot_line_chart(avg_mies_df, "Okres", "Srednia", None, "Średnia wartość transakcji", key_suffix="ogolna")

    if category_col == "Stacja":
        netto_bez_hois0_stacje = df_filtered[df_filtered["HOIS"] != 0].groupby(["Okres", "Stacja"])["Netto"].sum()
        transakcje_all_stacje = df_filtered.groupby(["Okres", "Stacja"])["#"].nunique()

        avg_mies_stacje_df = pd.concat([netto_bez_hois0_stacje, transakcje_all_stacje], axis=1).reset_index()
        avg_mies_stacje_df.columns = ["Okres", "Stacja", "Netto_bez_HOIS0", "Transakcje_all"]
        avg_mies_stacje_df["Srednia"] = avg_mies_stacje_df["Netto_bez_HOIS0"] / avg_mies_stacje_df["Transakcje_all"]

        plot_line_chart(avg_mies_stacje_df, "Okres", "Srednia", "Stacja", "Średnia wartość transakcji",
                        key_suffix="per_stacja")

    df_nonzero_hois = df_filtered[df_filtered["HOIS"] != 0].copy()

    excluded_products = [
        "myjnia jet zafiskalizowana",
        "opłata opak. kubek 0,25zł",
        "myjnia jet żeton"
    ]

    top_products = df_nonzero_hois[~df_nonzero_hois["Nazwa produktu"].str.lower().str.strip().isin(excluded_products)]
    top_products = top_products.groupby("Nazwa produktu")["Ilość"].sum().reset_index()
    top_products = top_products.sort_values(by="Ilość", ascending=False).head(10)

    if not top_products.empty:
        fig_top = px.bar(top_products, x="Nazwa produktu", y="Ilość",
                         title="Top 10 najlepiej sprzedających się produktów (bez HOIS 0)")
        plot_key_top = "Top 10 najlepiej sprzedających się produktów (bez HOIS 0)"
        st.session_state[f"fig_{plot_key_top}"] = fig_top
        col_plot, col_fav = st.columns([0.9, 0.1])
        with col_plot:
            st.plotly_chart(fig_top, use_container_width=True, key="top10_produkty")
        with col_fav:
            if st.button("★", key=f"fav_{plot_key_top}", help="Dodaj do ulubionych"):
                st.session_state.favorite_charts.add(plot_key_top)
                st.success(f"Dodano do ulubionych: {plot_key_top}")
    else:
        st.info("Brak danych do wygenerowania wykresu TOP 10.")

with tab3:
    st.header("Paliwo")
    st.subheader("Sprzedaż paliw")
    fuel_sales_grouped = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby(
        ["Okres"] + ([category_col] if category_col else []))["Ilość"].sum().reset_index()
    plot_line_chart(fuel_sales_grouped, "Okres", "Ilość", category_col, "Sprzedaż paliw")

    df_filtered["Typ klienta"] = df_filtered["B2B"].apply(lambda x: "B2B" if str(x).upper() == "TAK" else "B2C")
    customer_types = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby("Typ klienta")[
        "Ilość"].sum().reset_index()
    fig_customer_types = px.pie(customer_types, values="Ilość", names="Typ klienta",
                                title="Stosunek tankowań B2C do B2B", hole=0.4)
    fig_customer_types.update_traces(textposition='inside', textinfo='percent+label')
    st.session_state["fig_Stosunek tankowań B2C do B2B"] = fig_customer_types
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_customer_types, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Stosunek tankowań B2C do B2B", help="Dodaj do ulubionych"):
            st.session_state.favorite_charts.add("Stosunek tankowań B2C do B2B")
            st.success("Dodano do ulubionych: Stosunek tankowań B2C do B2B")

    fuel_data = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"]
    fuel_sales = fuel_data.groupby("Nazwa produktu")["Ilość"].sum().reset_index()
    fig_fuel = px.pie(fuel_sales, names="Nazwa produktu", values="Ilość", title="Udział produktów paliwowych")
    st.session_state["fig_Udział produktów paliwowych"] = fig_fuel
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_fuel, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Udział produktów paliwowych", help="Dodaj do ulubionych"):
            st.session_state.favorite_charts.add("Udział produktów paliwowych")
            st.success("Dodano do ulubionych: Udział produktów paliwowych")

with tab4:
    # 🥮 Metryki średniej penetracji lojalnościowej

        with st.container():
            st.subheader("📈 Średnia penetracja lojalnościowa")

            # Zakres obecny (z filtrów)
            start_date_current = pd.to_datetime(start_date)
            end_date_current = pd.to_datetime(end_date)

            df_loyal_current = df_filtered[
                (df_filtered["Karta lojalnościowa"].str.upper() == "TAK") &
                (pd.to_datetime(df_filtered["Data"]) >= start_date_current) &
                (pd.to_datetime(df_filtered["Data"]) <= end_date_current)
                ]
            df_total_current = df_filtered[
                (pd.to_datetime(df_filtered["Data"]) >= start_date_current) &
                (pd.to_datetime(df_filtered["Data"]) <= end_date_current)
                ]

            penetration_current = 0
            if not df_total_current.empty:
                penetration_current = df_loyal_current["#"].nunique() / df_total_current["#"].nunique() * 100

            # Zakres poprzedni (30 dni wcześniej)
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
            delta_color = "normal" if delta_value == 0 else "inverse" if delta_value > 0 else "off"
            prev_label = f"{start_date_prev.strftime('%d.%m')} - {end_date_prev.strftime('%d.%m')}"

            col_a, col_b = st.columns(2)
            col_a.metric(
                "Średnia penetracja (obecny zakres)",
                f"{penetration_current:.2f}%",
                delta=f"{delta_value:.2f}%",
                delta_color=delta_color
            )
            col_b.metric(f"Średnia penetracja ({prev_label})", f"{penetration_prev:.2f}%")

            # 📊 Penetracja lojalnościowa dziennie
            loyalty_df = df_filtered[df_filtered["Karta lojalnościowa"].str.upper() == "TAK"].copy()
            total_df = df_filtered.copy()

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
            fig_pen = style_plotly(fig_pen)

            # Dodaj do ulubionych: Penetracja lojalnościowa
            fav_pen_key = "Penetracja lojalnościowa (%)"
            st.session_state[f"fig_{fav_pen_key}"] = fig_pen
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_pen, use_container_width=True)
            with col_fav:
                if st.button("★", key=f"fav_{fav_pen_key}", help="Dodaj do ulubionych"):
                    st.session_state.favorite_charts.add(fav_pen_key)
                    st.success(f"Dodano do ulubionych: {fav_pen_key}")

            # 🔢 Liczba transakcji z kartą lojalnościową
            fig_loyal = px.line(loyal_daily, x="Okres", y="Lojalnościowe", title="Transakcje lojalnościowe")
            fig_loyal.update_traces(mode="lines+markers")
            fig_loyal.update_layout(xaxis_tickformat="%d.%m")
            for day in free_days:
                fig_loyal.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
            fig_loyal = style_plotly(fig_loyal)

            # Dodaj do ulubionych: Transakcje lojalnościowe
            fav_loyal_key = "Transakcje lojalnościowe"
            st.session_state[f"fig_{fav_loyal_key}"] = fig_loyal
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_loyal, use_container_width=True)
            with col_fav:
                if st.button("★", key=f"fav_{fav_loyal_key}", help="Dodaj do ulubionych"):
                    st.session_state.favorite_charts.add(fav_loyal_key)
                    st.success(f"Dodano do ulubionych: {fav_loyal_key}")

            # 🔄 Porównanie lojalnościowych vs wszystkich
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
            fig_combined = style_plotly(fig_combined)

            # Dodaj do ulubionych: Transakcje lojalnościowe vs. wszystkie
            fav_combined_key = "Transakcje lojalnościowe vs. wszystkie"
            st.session_state[f"fig_{fav_combined_key}"] = fig_combined
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_combined, use_container_width=True)
            with col_fav:
                if st.button("★", key=f"fav_{fav_combined_key}", help="Dodaj do ulubionych"):
                    st.session_state.favorite_charts.add(fav_combined_key)
                    st.success(f"Dodano do ulubionych: {fav_combined_key}")

        st.subheader("TOP / BOTTOM 5 grup towarowych wg penetracji lojalnościowej")

        df_loyal_top = df_filtered[df_filtered["Karta lojalnościowa"].str.upper() == "TAK"].copy()
        total_per_group = df_filtered.groupby("Grupa towarowa")["#"].nunique().reset_index(name="Total")
        loyal_per_group = df_loyal_top.groupby("Grupa towarowa")["#"].nunique().reset_index(name="Lojal")
        merged_top = pd.merge(total_per_group, loyal_per_group, on="Grupa towarowa", how="left")
        merged_top["Lojal"] = merged_top["Lojal"].fillna(0)
        merged_top = merged_top[~merged_top["Grupa towarowa"].str.contains("ZzzGrGSAP")]
        merged_top["Penetracja"] = (merged_top["Lojal"] / merged_top["Total"]) * 100
        merged_top = merged_top.sort_values("Penetracja", ascending=False)
        merged_top["Penetracja"] = merged_top["Penetracja"].round(2).astype(str) + "%"

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(merged_top.head(5).rename(columns={"Grupa towarowa": "Grupa"}))
        with col2:
            st.dataframe(merged_top.tail(5).rename(columns={"Grupa towarowa": "Grupa"}))

with tab5:
    st.header("Myjnia")
    carwash_df = df_filtered[df_filtered["Grupa sklepowa"] == "MYJNIA INNE"]
    if not carwash_df.empty:
        carwash_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[
            "Ilość"].sum().reset_index()
        plot_line_chart(carwash_grouped, "Okres", "Ilość", category_col, "Sprzedaż usług myjni")

        sales_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))[
            "Netto"].sum().reset_index()
        plot_line_chart(sales_grouped, "Okres", "Netto", category_col, "Sprzedaż netto grupy Myjnia")

        # Wykres karnetów w stosunku do reszty
        carwash_df["Typ produktu"] = carwash_df["Nazwa produktu"].str.lower().apply(
            lambda x: "Karnet" if x.startswith("karnet") else "Inne")
        pie_df = carwash_df.groupby("Typ produktu")["Ilość"].sum().reset_index()
        fig_karnet = px.pie(pie_df, values="Ilość", names="Typ produktu",
                            title="Udział karnetów w sprzedaży MYJNIA INNE", hole=0.4)
        fig_karnet.update_traces(textposition='inside', textinfo='percent+label')
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["fig_Udział karnetów w sprzedaży MYJNIA INNE"] = fig_karnet
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_karnet, use_container_width=True)
            with col_fav:
                if st.button("★", key="fav_Udział karnetów w sprzedaży MYJNIA INNE", help="Dodaj do ulubionych"):
                    st.session_state.favorite_charts.add("Udział karnetów w sprzedaży MYJNIA INNE")
                    st.success("Dodano do ulubionych: Udział karnetów w sprzedaży MYJNIA INNE")


        # Wykres udziału programów "myjnia express" i "myjnia standard" w całej grupie MYJNIA INNE
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

        with col2:
            st.session_state["fig_Udział programów Standard i Express w sprzedaży MYJNIA INNE"] = fig_program_all
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_program_all, use_container_width=True)
            with col_fav:
                if st.button("★", key="fav_Udział programów Standard i Express", help="Dodaj do ulubionych"):
                    st.session_state.favorite_charts.add("Udział programów Standard i Express w sprzedaży MYJNIA INNE")
                    st.success("Dodano do ulubionych: Udział programów Standard i Express w sprzedaży MYJNIA INNE")

with tab6:
    st.header("📌 Ulubione wykresy")
    favorites = st.session_state.get("favorite_charts", set())
    if not favorites:
        st.info("Nie dodano jeszcze żadnych wykresów do ulubionych.")
    else:
        st.write("Wybrane przez Ciebie wykresy:")
        for fav in list(favorites):
            st.markdown(f"### {fav}")
            st.plotly_chart(st.session_state.get(f"fig_{fav}"), use_container_width=True, key=f"ulubione_{fav}")
            if st.button("✖", key=f"remove_{fav}", help="Usuń z ulubionych"):
                favorites.remove(fav)
                st.session_state.favorite_charts = favorites
                st.rerun()

with tab7:
    st.header("Sprzedaż per kasjer")

    df_filtered["Kasjer"] = df_filtered["Stacja"].astype(str) + " - " + df_filtered["Login POS"].astype(str)

    # Metryki ogólne
    kasjer_summary = df_filtered.groupby("Kasjer").agg({
        "#": pd.Series.nunique,
        "Netto": "sum",
        "Ilość": "sum"
    }).reset_index()
    kasjer_summary.columns = ["Kasjer", "Liczba transakcji", "Obrót netto", "Suma sztuk"]
    kasjer_summary["Średnia wartość transakcji"] = kasjer_summary["Obrót netto"] / kasjer_summary["Liczba transakcji"]

    kasjer_summary = kasjer_summary.sort_values("Obrót netto", ascending=False)

    st.subheader("Ranking kasjerów wg obrotu netto")
    st.dataframe(kasjer_summary.head(20), use_container_width=True)

    # Wykres obrotu per kasjer (TOP 10)
    top10 = kasjer_summary.head(10)
    fig_kasjer = px.bar(top10, x="Kasjer", y="Obrót netto", title="TOP 10 kasjerów wg obrotu netto")
    st.plotly_chart(fig_kasjer, use_container_width=True)

    # Wykres liczby transakcji per kasjer (TOP 10)
    fig_trans = px.bar(top10, x="Kasjer", y="Liczba transakcji", title="TOP 10 kasjerów wg liczby transakcji")
    st.plotly_chart(fig_trans, use_container_width=True)

    # Wykres średniej wartości transakcji (TOP 10)
    fig_avg = px.bar(top10, x="Kasjer", y="Średnia wartość transakcji",
                     title="TOP 10 kasjerów wg średniej wartości transakcji")
    st.plotly_chart(fig_avg, use_container_width=True)


    #TOP PRODUKTY

    # 📊 Analiza top produktów per kasjer wg PLU

    st.subheader("📊 Analiza top produktów per kasjer (wg PLU)")

    # Wczytanie danych z pliku top produktów
    top_products_df = pd.read_csv("top_products.csv", sep=";")
    top_products_df["MIESIĄC"] = top_products_df["MIESIĄC"].astype(str)
    top_products_df["PLU"] = top_products_df["PLU"].astype(str)

    # Dodanie kolumny z miesiącem do danych sprzedażowych
    df_filtered["Miesiąc"] = pd.to_datetime(df_filtered["Data"]).dt.to_period("M").astype(str)
    df_filtered["PLU"] = df_filtered["PLU"].astype(str)

    # Wybór miesiąca do analizy
    dostepne_miesiace = sorted(top_products_df["MIESIĄC"].unique())
    wybrany_miesiac = st.selectbox("Wybierz miesiąc", dostepne_miesiace, index=len(dostepne_miesiace) - 1)

    # Lista top PLU dla danego miesiąca
    top_plu_list = top_products_df[top_products_df["MIESIĄC"] == wybrany_miesiac]["PLU"].tolist()
    nazwy_plu = top_products_df.set_index("PLU")["NAZWA"].to_dict()

    # Filtrowanie danych sprzedaży do top PLU
    df_top = df_filtered[
        (df_filtered["Miesiąc"] == wybrany_miesiac) &
        (df_filtered["PLU"].isin(top_plu_list))
        ].copy()

    if df_top.empty:
        st.warning("Brak danych dla top produktów w wybranym miesiącu.")
    else:
        # 👤 Kasjer = Stacja + Login POS
        df_top["Kasjer"] = df_top["Stacja"].astype(str) + " - " + df_top["Login POS"].astype(str)

        # 📈 Wykres 1: liczba sztuk per kasjer i produkt
        df_top["PLU_nazwa"] = df_top["PLU"].map(nazwy_plu)
        sztuki_df = df_top.groupby(["Kasjer", "PLU_nazwa"])["Ilość"].sum().reset_index()

        fig_top1 = px.bar(
            sztuki_df,
            x="Kasjer",
            y="Ilość",
            color="PLU_nazwa",
            title="Sprzedaż sztukowa top produktów per kasjer",
            text_auto=".2s"
        )
        st.plotly_chart(fig_top1, use_container_width=True)

        # 📊 Wykres 2: liczba sztuk na transakcję
        # Transakcje ogółem per kasjer
        transakcje_df = df_top.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Transakcje"})

        # Sprzedaż sztukowa per kasjer i top produkt
        sztuki_df = df_top.groupby(["Kasjer", "PLU_nazwa"])["Ilość"].sum().reset_index()

        # Połączenie – każdemu kasjerowi przypisujemy jego liczbę transakcji
        sztuki_df = sztuki_df.merge(transakcje_df, on="Kasjer", how="left")
        sztuki_df["Sztuki na transakcję"] = sztuki_df["Ilość"] / sztuki_df["Transakcje"]

        # 📊 Wykres
        fig_top2 = px.bar(
            sztuki_df,
            x="Kasjer",
            y="Sztuki na transakcję",
            color="PLU_nazwa",
            title="Średnia liczba sprzedanych top produktów na transakcję (per kasjer)",
            text_auto=".2f"
        )
        st.plotly_chart(fig_top2, use_container_width=True)

        # Penetracja per kasjer

        st.subheader("🎯 Penetracja lojalnościowa per kasjer")

        # Przygotowanie danych
        df_loyal = df_filtered[df_filtered["Karta lojalnościowa"].str.upper() == "TAK"].copy()
        df_all = df_filtered.copy()

        df_loyal["Kasjer"] = df_loyal["Stacja"].astype(str) + " - " + df_loyal["Login POS"].astype(str)
        df_all["Kasjer"] = df_all["Stacja"].astype(str) + " - " + df_all["Login POS"].astype(str)

        loyal_tx = df_loyal.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Lojalnościowe"})
        all_tx = df_all.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Wszystkie"})

        penetracja_df = pd.merge(all_tx, loyal_tx, on="Kasjer", how="left").fillna(0)
        penetracja_df["Penetracja"] = (penetracja_df["Lojalnościowe"] / penetracja_df["Wszystkie"]) * 100

        # Sortowanie malejąco
        penetracja_df = penetracja_df.sort_values("Penetracja", ascending=False)

        # Wykres
        fig_penetracja = px.bar(
            penetracja_df,
            x="Kasjer",
            y="Penetracja",
            title="Penetracja lojalnościowa per kasjer (%)",
            text_auto=".1f"
        )
        fig_penetracja.update_layout(yaxis_title="%", xaxis_title="Kasjer")

        st.plotly_chart(fig_penetracja, use_container_width=True)
