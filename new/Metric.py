from app import dcc, html, Input, Output

html.Div(f"Obrót netto (NFR+Fuel): {total_netto / 1_000_000:.1f} mln zł",
         style={'display': 'inline-block', 'marginRight': '20px', 'color': 'red'}),
html.Div(f"Unikalne transakcje: {total_transactions / 1000:,.0f} tys.",
         style={'display': 'inline-block', 'marginRight': '20px'}),
html.Div(f"Sprzedaż kawy: {round(kawa_netto / 1000):,} tys. zł",
         style={'display': 'inline-block', 'marginRight': '20px'}),
html.Div(f"Sprzedaż food: {round(food_netto / 1000):,} tys. zł",
         style={'display': 'inline-block', 'marginRight': '20px'}),
html.Div(f"Sprzedaż myjni: {round(myjnia_netto / 1000):,} tys. zł", style={'display': 'inline-block'})
class Metric( html.Div):

    def __init__(self):
        super(f"Obrót netto (NFR+Fuel): {total_netto / 1_000_000:.1f} mln zł",)



metric = Metric()