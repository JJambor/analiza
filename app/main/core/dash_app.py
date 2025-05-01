from main.meta.dash_meta import DashMeta
import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from main.utils.utils_functions import *

class DashApp():

    flask_app = None
    group_options = None
    station_options = None
    df = None
    app: dash.Dash = None
    df_cached = None
    hois_cached = None
    def __init__(self, flask_app, paths):
        super().__init__()
        self.flask_app = flask_app
        self.__initialize(paths)

    def get_dash_app(self) -> dash.Dash:
        return self.app



    def get_hois_map(self):
        return self.hois_map

    def get_df(self):
        return self.df

    def get_group_options(self):
        return self.df["Grupa towarowa"].unique().tolist()

    def get_station_options(self):
        return self.df["Stacja"].unique().tolist()

    def get_min_date(self):
        return self.df["Data"].min()

    def get_max_date(self):
        return self.df["Data"].max()

    def get_df_cached(self):
        return self.df_cached
    def get_hois_cached(self):
        return self.hois_cached
    def update_data(self, paths):
        # files = ["data01.xlsx"]
        files = paths.copy()
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
        self.df = df


    def _load_hois_map(self):
        file_path = "hois_map.csv"
        hois_df = pd.read_csv(file_path, encoding="utf-8", sep=";")
        hois_df.columns = [col.strip() for col in hois_df.columns]
        expected_columns = ["HOIS", "Grupa towarowa", "Grupa sklepowa"]
        actual_columns = hois_df.columns.tolist()
        if len(actual_columns) != len(expected_columns):
            raise Exception(f"Plik CSV powinien mieć kolumny: {expected_columns}, ale znaleziono: {actual_columns}")
        return {row["HOIS"]: (row["Grupa towarowa"], row["Grupa sklepowa"]) for _, row in hois_df.iterrows()}

    def _generate_metric_card(self, label, value, delta=None):
        formatted_value = format_metric_value(value) if isinstance(value, (int, float)) else value
        return html.Div(className="metric-card", children=[
            html.Div(label, className="metric-label"),
            html.Div(formatted_value, className="metric-value"),
            html.Div(delta if delta else "", className=f"metric-delta {'neutral' if not delta else ''}")
        ])

    def _map_cols(self):
        self.df["PLU_nazwa"] = self.df["PLU"].astype(str).str.strip() + " - " + self.df["Nazwa produktu"].astype(str).str.strip()
        self.df["Grupa towarowa"] = self.df["HOIS"].map(lambda x: self.hois_map.get(x, ("Nieznana", "Nieznana"))[0])
        self.df["Grupa sklepowa"] = self.df["HOIS"].map(lambda x: self.hois_map.get(x, ("Nieznana", "Nieznana"))[1])
    def reload(self, paths):

        self.update_data(paths)
        self.hois_map = self._load_hois_map()

        self._map_cols()
        self.df_cached = self.df.copy()
        self.hois_cached = self.hois_map.copy()

    def __initialize(self, paths):


        self.update_data(paths)
        self.hois_map = self._load_hois_map()

        self._map_cols()

        # first_day_last_month = get_last_day()
        # station_options = self.df["Stacja"].unique().tolist()
        # self.group_options = self.df["Grupa towarowa"].unique().tolist()

        self.df_cached = self.df.copy()
        self.hois_cached = self.hois_map.copy()
        self.__create_dash_app()

    def __create_dash_app(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            server=self.flask_app,
            url_base_pathname="/dashboard/",
            suppress_callback_exceptions=True,
            title="Kompas"
        )
        self.app.server.config['FAVORITES'] = set()
