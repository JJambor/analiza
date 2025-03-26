import streamlit as st
import pandas as pd
import plotly.express as px
import time
import uuid
import holidays

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

            df_month["Data"] = pd.to_datetime(df_month["Data"], errors="coerce")

            null_dates = df_month["Data"].isnull().sum()
            if null_dates > 0:
                st.warning(f"W pliku {file} znaleziono {null_dates} pustych lub błędnych dat.")

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
    df = df.dropna(subset=["Data"])
    df["Data"] = df["Data"].dt.date

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
selected_stations = station_options.tolist() if select_all_stations else st.sidebar.multiselect("Wybierz stacje", station_options, default=station_options)

group_options = df["Grupa towarowa"].unique()
select_all_groups = st.sidebar.checkbox("Zaznacz wszystkie grupy towarowe", value=True)
selected_groups = group_options.tolist() if select_all_groups else st.sidebar.multiselect("Wybierz grupy towarowe", group_options, default=group_options)

df_filtered = df[(df["Data"] >= start_date) & (df["Data"] <= end_date) & (df["Stacja"].isin(selected_stations)) & (df["Grupa towarowa"].isin(selected_groups))].copy()
df_filtered = df_filtered[df_filtered["Login POS"] != 99999].copy()

if df_filtered.empty:
    st.warning("Brak danych po zastosowaniu wybranych filtrów!")
    st.stop()

monthly_station_view = st.sidebar.checkbox("Widok miesięczny według stacji", value=False)
df_filtered["Okres"] = pd.to_datetime(df_filtered["Data"]).dt.to_period("M").astype(str) if monthly_station_view else df_filtered["Data"]
category_col = "Stacja" if monthly_station_view else None

# Dodaj zakładki, aby zdefiniować zmienną tab1 itd.
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Ogólny", "Sklep", "Paliwo", "Lojalność", "Myjnia"])

def plot_line_chart(df, x, y, color, title, key_suffix="", fill_area=False):
    fig = px.line(
        df, x=x, y=y, color=color, title=title, markers=True
    )

    # 📈 Styl linii
    line_mode = "lines+markers"
    line_shape = "spline"

    # 🔁 Warunkowe wypełnienie
    if fill_area:
        fig.update_traces(mode=line_mode, line_shape=line_shape, fill="tozeroy")
    else:
        fig.update_traces(mode=line_mode, line_shape=line_shape)

    # 🕓 Dni wolne
    try:
        start_date = pd.to_datetime(df[x].min())
        end_date = pd.to_datetime(df[x].max())
        free_days = get_free_days(start_date, end_date)

        for day in free_days:
            fig.add_vline(x=day, line_dash="dot", line_color="gray", opacity=0.2)
    except Exception as e:
        st.warning(f"Błąd przy dodawaniu dni wolnych: {e}")

    # 🎨 Styl
    hovertemplate = f"<b>{x}:</b> %{{x}}<br><b>{y}:</b> %{{y:.2f}}"
    fig = style_plotly(fig, hovertemplate)

    st.plotly_chart(fig, use_container_width=True, key=f"{title}_{key_suffix}")



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
        col1.metric("Obrót netto(NFR+Fuel)", f"{round(total_netto / 1000):,} tys. zł")
        col2.metric("Unikalne transakcje", total_transactions)
        col3.metric("Sprzedaż kawy", f"{round(kawa_netto / 1000):,} tys. zł")
        col4.metric("Sprzedaż food", f"{round(food_netto / 1000):,} tys. zł")
        col5.metric("Sprzedaż myjni", f"{round(myjnia_netto / 1000):,} tys. zł")

        plot_line_chart(
            df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index(),
            "Okres", "Netto", category_col, "Obrót netto (NFR+Fuel)")
        plot_line_chart(
            df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index(),
            "Okres", "#", category_col, "Liczba transakcji")

with tab2:
    st.header("Sklep")

    netto_bez_hois0 = df_filtered[df_filtered["HOIS"] != 0]["Netto"].sum()
    unikalne_transakcje = df_filtered["#"].nunique()
    avg_transaction = netto_bez_hois0 / unikalne_transakcje if unikalne_transakcje > 0 else 0

    st.metric("Średnia wartość transakcji (obrót bez HOIS 0 / wszystkie transakcje)", f"{avg_transaction:.2f} zł")

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

        plot_line_chart(avg_mies_stacje_df, "Okres", "Srednia", "Stacja", "Średnia wartość transakcji", key_suffix="per_stacja")

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
        st.plotly_chart(fig_top, use_container_width=True, key="top10_produkty")
    else:
        st.info("Brak danych do wygenerowania wykresu TOP 10.")


with tab3:
    st.header("Paliwo")
    st.subheader("Sprzedaż paliw")
    fuel_sales_grouped = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby(["Okres"] + ([category_col] if category_col else []))["Ilość"].sum().reset_index()
    plot_line_chart(fuel_sales_grouped, "Okres", "Ilość", category_col, "Sprzedaż paliw")

    st.subheader("Stosunek B2C do B2B")
    df_filtered["Typ klienta"] = df_filtered["B2B"].apply(lambda x: "B2B" if str(x).upper() == "TAK" else "B2C")
    customer_types = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"].groupby("Typ klienta")["Ilość"].sum().reset_index()
    fig_customer_types = px.pie(customer_types, values="Ilość", names="Typ klienta", title="Stosunek tankowań B2C do B2B", hole=0.4)
    fig_customer_types.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_customer_types, use_container_width=True)

    st.subheader("Udział produktów paliwowych")
    fuel_data = df_filtered[df_filtered["Grupa sklepowa"] == "PALIWO"]
    fuel_sales = fuel_data.groupby("Nazwa produktu")["Ilość"].sum().reset_index()
    fig_fuel = px.pie(fuel_sales, names="Nazwa produktu", values="Ilość", title="Udział produktów paliwowych")
    st.plotly_chart(fig_fuel, use_container_width=True)

with tab4:
    st.header("Lojalność")
    loyalty_df = df_filtered[df_filtered["Karta lojalnościowa"].str.upper() == "TAK"].groupby(
        ["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index()
    total_df = df_filtered.groupby(["Okres"] + ([category_col] if category_col else []))["#"].nunique().reset_index()
    merged_df = pd.merge(loyalty_df, total_df, on=["Okres"] + ([category_col] if category_col else []),
                         suffixes=("_loyal", "_total"))
    merged_df["Penetracja"] = (merged_df["#_loyal"] / merged_df["#_total"]) * 100
    plot_line_chart(merged_df, "Okres", "Penetracja", category_col, "Penetracja lojalnościowa (%)")
with tab5:
    st.header("Myjnia")
    carwash_df = df_filtered[df_filtered["Grupa sklepowa"] == "MYJNIA INNE"]
    if not carwash_df.empty:
        carwash_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))["Ilość"].sum().reset_index()
        plot_line_chart(carwash_grouped, "Okres", "Ilość", category_col, "Sprzedaż usług myjni")

        sales_grouped = carwash_df.groupby(["Okres"] + ([category_col] if category_col else []))["Netto"].sum().reset_index()
        plot_line_chart(sales_grouped, "Okres", "Netto", category_col, "Sprzedaż netto grupy Myjnia")

        # Wykres karnetów w stosunku do reszty
        carwash_df["Typ produktu"] = carwash_df["Nazwa produktu"].str.lower().apply(lambda x: "Karnet" if x.startswith("karnet") else "Inne")
        pie_df = carwash_df.groupby("Typ produktu")["Ilość"].sum().reset_index()
        fig_karnet = px.pie(pie_df, values="Ilość", names="Typ produktu", title="Udział karnetów w sprzedaży MYJNIA INNE", hole=0.4)
        fig_karnet.update_traces(textposition='inside', textinfo='percent+label')
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_karnet, use_container_width=True)

        # Wykres programów 1 i 2 w stosunku do reszty (bez karnetów)
        non_karnet_df = carwash_df[~carwash_df["Nazwa produktu"].str.lower().str.startswith("karnet")].copy()
        def classify_program(nazwa):
            nazwa = nazwa.lower()
            if any(prog in nazwa for prog in ["błysk", "ultra błysk", "extra"]):
                return "Program 1/2"
            return "Inne"

        non_karnet_df["Program"] = non_karnet_df["Nazwa produktu"].apply(classify_program)
        program_df = non_karnet_df.groupby("Program")["Ilość"].sum().reset_index()
        fig_program = px.pie(program_df, values="Ilość", names="Program", title="Udział programów 1 i 2 w sprzedaży MYJNIA INNE (bez karnetów)", hole=0.4)
        fig_program.update_traces(textposition='inside', textinfo='percent+label')
        with col2:
            st.plotly_chart(fig_program, use_container_width=True)
    else:
        st.info("Brak danych o myjni w wybranym zakresie.")
