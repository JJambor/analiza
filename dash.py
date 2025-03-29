import streamlit as st
import pandas as pd
import plotly.express as px
import time
import holidays

st.set_page_config(layout="wide")


def get_free_days(start_date, end_date):
    pl_holidays = holidays.Poland(years=range(start_date.year, end_date.year + 1))
    date_range = pd.date_range(start=start_date, end=end_date)
    return [date for date in date_range if date.weekday() >= 5 or date in pl_holidays]


def style_plotly(fig, hovertemplate=None):
    custom_colors = px.colors.qualitative.Set2
    fig.update_layout(colorway=custom_colors)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=14),
        hovermode="x unified"
    )
    if hovertemplate:
        fig.update_traces(hovertemplate=hovertemplate)
    return fig


@st.cache_data(ttl=3600, show_spinner="Ładowanie mapy HOIS...")
def load_hois_map():
    try:
        file_path = "hois_map.csv"
        hois_df = pd.read_csv(file_path, encoding="utf-8", sep=";")
        hois_df.columns = [col.strip() for col in hois_df.columns]
        expected_columns = ["HOIS", "Grupa towarowa", "Grupa sklepowa"]
        if not all(col in hois_df.columns for col in expected_columns):
            st.error(f"Plik CSV powinien mieć kolumny: {expected_columns}, ale znaleziono: {hois_df.columns.tolist()}")
            return {}
        return dict(zip(hois_df["HOIS"].astype(str), zip(hois_df["Grupa towarowa"], hois_df["Grupa sklepowa"])))
    except Exception as e:
        st.error(f"Błąd wczytywania mapy HOIS: {e}")
        return {}


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
            df_month["Data_full"] = pd.to_datetime(df_month["Data"], errors="coerce")
            null_dates = df_month["Data_full"].isnull().sum()
            if null_dates > 0:
                st.warning(f"W pliku {file} znaleziono {null_dates} pustych lub błędnych dat.")
            df_month["Data"] = df_month["Data_full"].dt.date
            dfs.append(df_month)
            with st.container():
                placeholder = st.empty()
                placeholder.markdown(f"""
                    <div style='margin-top: 30px;'>
                        <p style='color: green; font-weight: bold;'>Wczytano poprawnie {file}, {len(df_month)} wierszy.</p>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                placeholder.empty()
        except Exception as e:
            st.error(f"Błąd przy wczytywaniu {file}: {e}")
    if not dfs:
        st.error("Brak poprawnych danych do połączenia!")
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).dropna(subset=["Data_full"])


# Wczytanie danych raz
hois_map = load_hois_map()
df = load_data()

if df.empty or df["Data"].isnull().all():
    st.error("Dane są puste lub wszystkie daty są niepoprawne!")
    st.stop()

# Przygotowanie danych na starcie
df["HOIS"] = df["HOIS"].astype(str)
df["PLU"] = df["PLU"].astype(str)
df["Stacja"] = df["Stacja"].astype(str)
df["Login POS"] = df["Login POS"].astype(str)
df["Grupa towarowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[0])
df["Grupa sklepowa"] = df["HOIS"].map(lambda x: hois_map.get(x, ("Nieznana", "Nieznana"))[1])

# Filtry w sidebarze
st.sidebar.header("Filtry")
start_date = st.sidebar.date_input("Od", df["Data"].min())
end_date = st.sidebar.date_input("Do", df["Data"].max())
station_options = df["Stacja"].unique()
select_all_stations = st.sidebar.checkbox("Zaznacz wszystkie stacje", value=True)
selected_stations = station_options.tolist() if select_all_stations else st.sidebar.multiselect("Wybierz stacje", station_options, default=station_options)
group_options = df["Grupa towarowa"].unique()
select_all_groups = st.sidebar.checkbox("Zaznacz wszystkie grupy towarowe", value=True)
selected_groups = group_options.tolist() if select_all_groups else st.sidebar.multiselect("Wybierz grupy towarowe", group_options, default=group_options)

# Filtrowanie danych
df_filtered = df[
    (df["Data"] >= start_date) &
    (df["Data"] <= end_date) &
    (df["Stacja"].isin(selected_stations)) &
    (df["Grupa towarowa"].isin(selected_groups)) &
    (df["Login POS"] != "99999")
]

if df_filtered.empty:
    st.warning("Brak danych po zastosowaniu filtrów!")
    st.stop()

# Przygotowanie kolumn
monthly_station_view = st.sidebar.checkbox("Widok miesięczny według stacji", value=False, key="checkbox_miesieczny")
df_filtered["Okres"] = pd.to_datetime(df_filtered["Data"]).dt.to_period("M").astype(str) if monthly_station_view else df_filtered["Data"]
category_col = "Stacja" if isinstance(df_filtered["Okres"].iloc[0], str) else None

df_filtered["Typ klienta"] = df_filtered["B2B"].apply(lambda x: "B2B" if str(x).upper() == "TAK" else "B2C")
df_filtered["Godzina"] = pd.to_datetime(df_filtered["Data_full"]).dt.hour
df_filtered["Dzień tygodnia"] = pd.to_datetime(df_filtered["Data_full"]).dt.dayofweek
df_filtered["Miesiąc"] = pd.to_datetime(df_filtered["Data"]).dt.to_period("M").astype(str)
df_filtered["Kasjer"] = df_filtered["Stacja"] + " - " + df_filtered["Login POS"]
df_filtered["PLU_nazwa"] = df_filtered.get("Nazwa produktu", pd.Series(dtype="str")).astype(str)
df_filtered["Netto_bez_HOIS0"] = df_filtered[df_filtered["HOIS"] != "0"]["Netto"]
df_filtered["Średnia transakcja"] = df_filtered["Netto_bez_HOIS0"] / df_filtered["#"].nunique()
df_filtered["Karta_TAK"] = df_filtered["Karta lojalnościowa"].str.upper() == "TAK"

# Przygotowanie danych lojalnościowych
loyalty_df = df_filtered[df_filtered["Karta_TAK"]]
total_df = df_filtered
loyal_daily = loyalty_df.groupby("Okres")["#"].nunique().reset_index(name="Lojalnościowe")
total_daily = total_df.groupby("Okres")["#"].nunique().reset_index(name="Wszystkie")
merged_top = df_filtered.groupby("Grupa towarowa").agg({"#": pd.Series.nunique}).rename(columns={"#": "Total"}).merge(
    loyalty_df.groupby("Grupa towarowa").agg({"#": pd.Series.nunique}).rename(columns={"#": "Lojal"}), 
    on="Grupa towarowa", how="left"
).fillna({"Lojal": 0})
merged_top = merged_top[~merged_top.index.str.contains("ZzzGrGSAP")]
merged_top["Penetracja"] = (merged_top["Lojal"] / merged_top["Total"] * 100).round(2).astype(str) + "%"

# Dane myjni
carwash_df = df_filtered[df_filtered["Grupa sklepowa"] == "MYJNIA INNE"]
carwash_df["Typ produktu"] = carwash_df["Nazwa produktu"].str.lower().apply(
    lambda x: "Karnet" if isinstance(x, str) and x.startswith("karnet") else "Inne"
)
carwash_df["Program"] = carwash_df["Nazwa produktu"].apply(
    lambda x: "Myjnia Standard" if "standard" in str(x).lower() else ("Myjnia Express" if "express" in str(x).lower() else "Pozostałe")
)

# Inicjalizacja ulubionych
if "favorite_charts" not in st.session_state:
    st.session_state.favorite_charts = set()

# Zakładki
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Ogólny", "Sklep", "Paliwo", "Lojalność", "Myjnia", "Ulubione", "Sprzedaż per kasjer"]
)


def plot_line_chart(df, x, y, color, title, key_suffix="", fill_area=False):
    try:
        fig = px.line(df, x=x, y=y, color=color, title=title, markers=True)
        line_mode = "lines+markers"
        line_shape = "spline"
        if fill_area:
            fig.update_traces(mode=line_mode, line_shape=line_shape, fill="tozeroy")
        else:
            fig.update_traces(mode=line_mode, line_shape=line_shape)
        start_date = pd.to_datetime(df[x].min())
        end_date = pd.to_datetime(df[x].max())
        free_days = get_free_days(start_date, end_date)
        for day in free_days:
            fig.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
        hovertemplate = f"<b>{x}:</b> %{{x}}<br><b>{y}:</b> %{{y:.2f}}"
        fig = style_plotly(fig, hovertemplate)

        col_plot, col_fav = st.columns([0.9, 0.1])
        plot_key = f"{title}_{key_suffix}"
        with col_plot:
            st.plotly_chart(fig, use_container_width=True, key=plot_key)
        st.session_state[f"fig_{plot_key}"] = fig
        with col_fav:
            fav_key = f"{title}_{key_suffix}"
            if st.button("★", key=f"fav_btn_{fav_key}"):
                if fav_key in st.session_state.favorite_charts:
                    st.session_state.favorite_charts.remove(fav_key)
                    st.success(f"Usunięto z ulubionych: {title}")
                else:
                    st.session_state.favorite_charts.add(fav_key)
                    st.success(f"Dodano do ulubionych: {title}")
    except Exception as e:
        st.error(f"Błąd w generowaniu wykresu {title}: {e}")


with tab1:
    st.header("Ogólny")
    total_netto = df_filtered["Netto"].sum()
    total_transactions = df_filtered["#"].nunique()
    kawa_netto = df_filtered[df_filtered["Grupa sklepowa"] == "NAPOJE GORĄCE"]["Netto"].sum()
    food_netto = df_filtered[df_filtered["Grupa towarowa"].str.strip().str.upper().isin(["FOOD SERVICE", "USLUGI DODATKOWE"])]["Netto"].sum()
    myjnia_netto = df_filtered[df_filtered["Grupa sklepowa"] == "MYJNIA INNE"]["Netto"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Obrót netto(NFR+Fuel)", f"{round(total_netto / 1000):,} tys. zł")
    col2.metric("Unikalne transakcje", total_transactions)
    col3.metric("Sprzedaż kawy", f"{round(kawa_netto / 1000):,} tys. zł")
    col4.metric("Sprzedaż food", f"{round(food_netto / 1000):,} tys. zł")
    col5.metric("Sprzedaż myjni", f"{round(myjnia_netto / 1000):,} tys. zł")

    plot_line_chart(
        df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index(),
        "Okres", "Netto", category_col, "Obrót netto (NFR+Fuel)"
    )
    plot_line_chart(
        df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index(),
        "Okres", "#", category_col, "Liczba transakcji"
    )

    st.subheader("Heatmapa transakcji – dzień tygodnia vs godzina")
    selected_metric = st.radio(
        "Wybierz metrykę do analizy:",
        options=["Liczba transakcji", "Obrót netto", "Liczba sztuk", "Transakcje paliwowe", "Penetracja lojalnościowa"],
        horizontal=True
    )

    dni = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
    godziny = list(range(24))
    full_index = pd.MultiIndex.from_product([range(7), godziny], names=["Dzień tygodnia", "Godzina"])

    if selected_metric == "Liczba transakcji":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
    elif selected_metric == "Obrót netto":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["Netto"].sum()
    elif selected_metric == "Liczba sztuk":
        df_grouped = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["Ilość"].sum()
    elif selected_metric == "Transakcje paliwowe":
        df_grouped = df_filtered[df_filtered["HOIS"] == "0"].groupby(["Dzień tygodnia", "Godzina"])["#"].nunique()
    else:
        all_tx = df_filtered.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique().rename("Wszystkie")
        loyal_tx = loyalty_df.groupby(["Dzień tygodnia", "Godzina"])["#"].nunique().rename("Lojalnościowe")
        merged = pd.merge(all_tx, loyal_tx, left_index=True, right_index=True, how="left").fillna(0)
        df_grouped = merged["Lojalnościowe"] / merged["Wszystkie"] * 100

    df_grouped = df_grouped.reindex(full_index, fill_value=0).reset_index(name="Wartość")
    heat_pivot = df_grouped.pivot(index="Dzień tygodnia", columns="Godzina", values="Wartość")
    heat_pivot.index = [dni[i] for i in heat_pivot.index]

    fig_heatmap = px.imshow(
        heat_pivot,
        labels=dict(x="Godzina", y="Dzień tygodnia", color=selected_metric),
        x=[str(g) for g in godziny],
        aspect="auto",
        color_continuous_scale="Blues",
        title=f"📊 Heatmapa – {selected_metric}"
    )
    fig_heatmap.update_layout(xaxis_title="Godzina dnia", yaxis_title="Dzień tygodnia", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_heatmap, use_container_width=True)


with tab2:
    st.header("Sklep")
    netto_bez_hois0 = df_filtered[df_filtered["HOIS"] != "0"]["Netto"].sum()
    unikalne_transakcje = df_filtered["#"].nunique()
    avg_transaction = netto_bez_hois0 / unikalne_transakcje if unikalne_transakcje > 0 else 0

    st.metric("Średnia wartość transakcji (obrót bez HOIS 0 / wszystkie transakcje)", f"{avg_transaction:.2f} zł")

    avg_mies_df = df_filtered[df_filtered["HOIS"] != "0"].groupby("Okres").agg({"Netto": "sum", "#": pd.Series.nunique}).reset_index()
    avg_mies_df["Srednia"] = avg_mies_df["Netto"] / avg_mies_df["#"]
    plot_line_chart(avg_mies_df, "Okres", "Srednia", None, "Średnia wartość transakcji", key_suffix="ogolna")

    if category_col == "Stacja":
        avg_mies_stacje_df = df_filtered[df_filtered["HOIS"] != "0"].groupby(["Okres", "Stacja"]).agg({"Netto": "sum", "#": pd.Series.nunique}).reset_index()
        avg_mies_stacje_df["Srednia"] = avg_mies_stacje_df["Netto"] / avg_mies_stacje_df["#"]
        plot_line_chart(avg_mies_stacje_df, "Okres", "Srednia", "Stacja", "Średnia wartość transakcji", key_suffix="per_stacja")

    df_nonzero_hois = df_filtered[df_filtered["HOIS"] != "0"]
    excluded_products = ["myjnia jet zafiskalizowana", "opłata opak. kubek 0,25zł", "myjnia jet żeton"]
    top_products = df_nonzero_hois[~df_nonzero_hois["Nazwa produktu"].str.lower().str.strip().isin(excluded_products)]
    top_products = top_products.groupby("Nazwa produktu")["Ilość"].sum().nlargest(10).reset_index()

    if not top_products.empty:
        fig_top = px.bar(top_products, x="Nazwa produktu", y="Ilość", title="Top 10 najlepiej sprzedających się produktów (bez HOIS 0)")
        st.session_state["fig_Top 10 najlepiej sprzedających się produktów (bez HOIS 0)"] = fig_top
        col_plot, col_fav = st.columns([0.9, 0.1])
        with col_plot:
            st.plotly_chart(fig_top, use_container_width=True)
        with col_fav:
            if st.button("★", key="fav_Top 10 najlepiej sprzedających się produktów (bez HOIS 0)"):
                st.session_state.favorite_charts.add("Top 10 najlepiej sprzedających się produktów (bez HOIS 0)")
                st.success("Dodano do ulubionych")
    else:
        st.info("Brak danych do wygenerowania wykresu TOP 10.")


with tab3:
    st.header("Paliwo")
    st.subheader("Sprzedaż paliw")
    fuel_sales_grouped = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby(
        ["Okres"] + ([category_col] if category_col else []))["Ilość"].sum().reset_index()
    plot_line_chart(fuel_sales_grouped, "Okres", "Ilość", category_col, "Sprzedaż paliw")

    customer_types = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby("Typ klienta")["Ilość"].sum().reset_index()
    fig_customer_types = px.pie(customer_types, values="Ilość", names="Typ klienta", title="Stosunek tankowań B2C do B2B", hole=0.4)
    fig_customer_types.update_traces(textposition='inside', textinfo='percent+label')
    st.session_state["fig_Stosunek tankowań B2C do B2B"] = fig_customer_types
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_customer_types, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Stosunek tankowań B2C do B2B"):
            st.session_state.favorite_charts.add("Stosunek tankowań B2C do B2B")
            st.success("Dodano do ulubionych")

    fuel_sales = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby("Nazwa produktu")["Ilość"].sum().reset_index()
    fig_fuel = px.pie(fuel_sales, names="Nazwa produktu", values="Ilość", title="Udział produktów paliwowych")
    st.session_state["fig_Udział produktów paliwowych"] = fig_fuel
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_fuel, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Udział produktów paliwowych"):
            st.session_state.favorite_charts.add("Udział produktów paliwowych")
            st.success("Dodano do ulubionych")


with tab4:
    st.subheader("📈 Średnia penetracja lojalnościowa")
    start_date_current = pd.to_datetime(start_date)
    end_date_current = pd.to_datetime(end_date)
    df_loyal_current = df_filtered[df_filtered["Karta_TAK"] & (pd.to_datetime(df_filtered["Data"]) >= start_date_current) & (pd.to_datetime(df_filtered["Data"]) <= end_date_current)]
    df_total_current = df_filtered[(pd.to_datetime(df_filtered["Data"]) >= start_date_current) & (pd.to_datetime(df_filtered["Data"]) <= end_date_current)]
    penetration_current = df_loyal_current["#"].nunique() / df_total_current["#"].nunique() * 100 if not df_total_current.empty else 0

    start_date_prev = start_date_current - pd.Timedelta(days=30)
    end_date_prev = start_date_current - pd.Timedelta(days=1)
    df_prev_filtered = df[
        (df["Data"] >= start_date_prev.date()) &
        (df["Data"] <= end_date_prev.date()) &
        (df["Stacja"].isin(selected_stations)) &
        (df["Grupa towarowa"].isin(selected_groups)) &
        (df["Login POS"] != "99999")
    ]
    df_loyal_prev = df_prev_filtered[df_prev_filtered["Karta lojalnościowa"].str.upper() == "TAK"]
    penetration_prev = df_loyal_prev["#"].nunique() / df_prev_filtered["#"].nunique() * 100 if not df_prev_filtered.empty else 0

    delta_value = penetration_current - penetration_prev
    delta_color = "normal" if delta_value == 0 else "inverse" if delta_value > 0 else "off"
    prev_label = f"{start_date_prev.strftime('%d.%m')} - {end_date_prev.strftime('%d.%m')}"

    col_a, col_b = st.columns(2)
    col_a.metric("Średnia penetracja (obecny zakres)", f"{penetration_current:.2f}%", delta=f"{delta_value:.2f}%", delta_color=delta_color)
    col_b.metric(f"Średnia penetracja ({prev_label})", f"{penetration_prev:.2f}%")

    merged_df = pd.merge(loyal_daily, total_daily, on="Okres")
    merged_df["Penetracja"] = (merged_df["Lojalnościowe"] / merged_df["Wszystkie"]) * 100
    pl_holidays = holidays.Poland()
    free_days = [day for day in pd.to_datetime(merged_df["Okres"]).dt.date.unique() if day.weekday() >= 5 or day in pl_holidays]
    fig_pen = px.line(merged_df, x="Okres", y="Penetracja", title="Penetracja lojalnościowa (%)")
    fig_pen.update_traces(mode="lines+markers")
    for day in free_days:
        fig_pen.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
    fig_pen = style_plotly(fig_pen)
    st.session_state["fig_Penetracja lojalnościowa (%)"] = fig_pen
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_pen, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Penetracja lojalnościowa (%)"):
            st.session_state.favorite_charts.add("Penetracja lojalnościowa (%)")
            st.success("Dodano do ulubionych")

    fig_loyal = px.line(loyal_daily, x="Okres", y="Lojalnościowe", title="Transakcje lojalnościowe")
    fig_loyal.update_traces(mode="lines+markers")
    for day in free_days:
        fig_loyal.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
    fig_loyal = style_plotly(fig_loyal)
    st.session_state["fig_Transakcje lojalnościowe"] = fig_loyal
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_loyal, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Transakcje lojalnościowe"):
            st.session_state.favorite_charts.add("Transakcje lojalnościowe")
            st.success("Dodano do ulubionych")

    df_both_melted = merged_df.melt(id_vars=["Okres"], value_vars=["Lojalnościowe", "Wszystkie"], var_name="Typ transakcji", value_name="Liczba")
    fig_combined = px.line(df_both_melted, x="Okres", y="Liczba", color="Typ transakcji", title="Transakcje lojalnościowe vs. wszystkie")
    fig_combined.update_traces(mode="lines+markers")
    fig_combined.update_layout(yaxis2=dict(title="Lojalnościowe transakcje", overlaying="y", side="right", showgrid=False))
    fig_combined.for_each_trace(lambda trace: trace.update(yaxis="y2") if trace.name == "Lojalnościowe" else None)
    for day in free_days:
        fig_combined.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
    fig_combined = style_plotly(fig_combined)
    st.session_state["fig_Transakcje lojalnościowe vs. wszystkie"] = fig_combined
    col_plot, col_fav = st.columns([0.9, 0.1])
    with col_plot:
        st.plotly_chart(fig_combined, use_container_width=True)
    with col_fav:
        if st.button("★", key="fav_Transakcje lojalnościowe vs. wszystkie"):
            st.session_state.favorite_charts.add("Transakcje lojalnościowe vs. wszystkie")
            st.success("Dodano do ulubionych")


with tab5:
    st.header("Myjnia")
    if not carwash_df.empty:
        carwash_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))["Ilość"].sum().reset_index()
        plot_line_chart(carwash_grouped, "Okres", "Ilość", category_col, "Sprzedaż usług myjni")

        sales_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index()
        plot_line_chart(sales_grouped, "Okres", "Netto", category_col, "Sprzedaż netto grupy Myjnia")

        pie_df = carwash_df.groupby("Typ produktu")["Ilość"].sum().reset_index()
        fig_karnet = px.pie(pie_df, values="Ilość", names="Typ produktu", title="Udział karnetów w sprzedaży MYJNIA INNE", hole=0.4)
        fig_karnet.update_traces(textposition='inside', textinfo='percent+label')
        st.session_state["fig_Udział karnetów w sprzedaży MYJNIA INNE"] = fig_karnet
        col1, col2 = st.columns(2)
        with col1:
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_karnet, use_container_width=True)
            with col_fav:
                if st.button("★", key="fav_Udział karnetów w sprzedaży MYJNIA INNE"):
                    st.session_state.favorite_charts.add("Udział karnetów w sprzedaży MYJNIA INNE")
                    st.success("Dodano do ulubionych")

        program_df_all = carwash_df.groupby("Program")["Ilość"].sum().reset_index()
        fig_program_all = px.pie(program_df_all, values="Ilość", names="Program", title="Udział programów Standard i Express w sprzedaży MYJNIA INNE", hole=0.4)
        fig_program_all.update_traces(textposition='inside', textinfo='percent+label')
        st.session_state["fig_Udział programów Standard i Express w sprzedaży MYJNIA INNE"] = fig_program_all
        with col2:
            col_plot, col_fav = st.columns([0.9, 0.1])
            with col_plot:
                st.plotly_chart(fig_program_all, use_container_width=True)
            with col_fav:
                if st.button("★", key="fav_Udział programów Standard i Express"):
                    st.session_state.favorite_charts.add("Udział programów Standard i Express w sprzedaży MYJNIA INNE")
                    st.success("Dodano do ulubionych")


with tab6:
    st.header("📌 Ulubione wykresy")
    favorites = st.session_state.get("favorite_charts", set())
    if not favorites:
        st.info("Nie dodano jeszcze żadnych wykresów do ulubionych.")
    else:
        for fav in list(favorites):
            st.markdown(f"### {fav}")
            st.plotly_chart(st.session_state.get(f"fig_{fav}"), use_container_width=True, key=f"ulubione_{fav}")
            if st.button("✖", key=f"remove_{fav}", help="Usuń z ulubionych"):
                st.session_state.favorite_charts.remove(fav)
                st.rerun()


with tab7:
    st.header("Sprzedaż per kasjer")
    kasjer_summary = df_filtered.groupby("Kasjer").agg({"#": pd.Series.nunique, "Netto": "sum", "Ilość": "sum"}).reset_index()
    kasjer_summary.columns = ["Kasjer", "Liczba transakcji", "Obrót netto", "Suma sztuk"]
    kasjer_summary["Średnia wartość transakcji"] = kasjer_summary["Obrót netto"] / kasjer_summary["Liczba transakcji"]
    kasjer_summary = kasjer_summary.sort_values("Obrót netto", ascending=False)

    st.subheader("Ranking kasjerów wg obrotu netto")
    st.dataframe(kasjer_summary.head(20), use_container_width=True)

    top10 = kasjer_summary.head(10)
    fig_kasjer = px.bar(top10, x="Kasjer", y="Obrót netto", title="TOP 10 kasjerów wg obrotu netto")
    st.plotly_chart(fig_kasjer, use_container_width=True)

    fig_trans = px.bar(top10, x="Kasjer", y="Liczba transakcji", title="TOP 10 kasjerów wg liczby transakcji")
    st.plotly_chart(fig_trans, use_container_width=True)

    fig_avg = px.bar(top10, x="Kasjer", y="Średnia wartość transakcji", title="TOP 10 kasjerów wg średniej wartości transakcji")
    st.plotly_chart(fig_avg, use_container_width=True)

    st.subheader("📊 Analiza top produktów per kasjer (wg PLU)")
    try:
        top_products_df = pd.read_csv("top_products.csv", sep=";")
        top_products_df["MIESIĄC"] = top_products_df["MIESIĄC"].astype(str)
        top_products_df["PLU"] = top_products_df["PLU"].astype(str)
    except Exception as e:
        st.error(f"Błąd wczytywania top_products.csv: {e}")
        top_products_df = pd.DataFrame()

    if not top_products_df.empty:
        dostepne_miesiace = sorted(top_products_df["MIESIĄC"].unique())
        wybrany_miesiac = st.selectbox("Wybierz miesiąc", dostepne_miesiace, index=len(dostepne_miesiace) - 1)
        top_plu_list = top_products_df[top_products_df["MIESIĄC"] == wybrany_miesiac]["PLU"].tolist()
        nazwy_plu = top_products_df.set_index("PLU")["NAZWA"].to_dict()

        df_top = df_filtered[(df_filtered["Miesiąc"] == wybrany_miesiac) & (df_filtered["PLU"].isin(top_plu_list))]
        if not df_top.empty:
            df_top["PLU_nazwa"] = df_top["PLU"].map(nazwy_plu)
            sztuki_df = df_top.groupby(["Kasjer", "PLU_nazwa"])["Ilość"].sum().reset_index()
            fig_top1 = px.bar(sztuki_df, x="Kasjer", y="Ilość", color="PLU_nazwa", title="Sprzedaż sztukowa top produktów per kasjer", text_auto=".2s")
            st.plotly_chart(fig_top1, use_container_width=True)

            transakcje_df = df_top.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Transakcje"})
            sztuki_df = sztuki_df.merge(transakcje_df, on="Kasjer", how="left")
            sztuki_df["Sztuki na transakcję"] = sztuki_df["Ilość"] / sztuki_df["Transakcje"]
            fig_top2 = px.bar(sztuki_df, x="Kasjer", y="Sztuki na transakcję", color="PLU_nazwa", title="Średnia liczba sprzedanych top produktów na transakcję (per kasjer)", text_auto=".2f")
            st.plotly_chart(fig_top2, use_container_width=True)

        st.subheader("🎯 Penetracja lojalnościowa per kasjer")
        loyal_tx = loyalty_df.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Lojalnościowe"})
        all_tx = df_filtered.groupby("Kasjer")["#"].nunique().reset_index().rename(columns={"#": "Wszystkie"})
        penetracja_df = pd.merge(all_tx, loyal_tx, on="Kasjer", how="left").fillna(0)
        penetracja_df["Penetracja"] = (penetracja_df["Lojalnościowe"] / penetracja_df["Wszystkie"]) * 100
        penetracja_df = penetracja_df.sort_values("Penetracja", ascending=False)
        fig_penetracja = px.bar(penetracja_df, x="Kasjer", y="Penetracja", title="Penetracja lojalnościowa per kasjer (%)", text_auto=".1f")
        st.plotly_chart(fig_penetracja, use_container_width=True)
    else:
        st.warning("Brak danych top produktów.")
