import plotly.io as pio

def create_templates():
    corporate_blue_palette = [
        "#0F4C81",  # Dark navy Blue
        "#2A9D8F",  # Soft navy
        "#A8DADC",  # Light Aqua
        "#E9F5FB",  # Very Light Blue
        "#457B9D",  # Blue Steel
        "#1D3557",  # Deep Blue
        "#74C0FC",  # Sky Blue Accent
        "#BFD7EA",  # Soft Grayish Blue
        "#F1FAFB",  # Almost White
        "#5DADE2",  # Brighter Blue Accent
    ]

    pio.templates["corporate_blue"] = pio.templates["plotly_white"]
    pio.templates["corporate_blue"]["layout"]["colorway"] = corporate_blue_palette
    pio.templates["corporate_blue"]["layout"]["font"] = {
        "family": "Segoe UI, Open Sans, sans-serif",
        "size": 15,
        "color": "#1D3557"
    }
    pio.templates["corporate_blue"]["layout"]["title"] = {
        "x": 0.05,
        "xanchor": "left",
        "font": {
            "size": 20,
            "color": "#0F4C81",
            "family": "Segoe UI Semibold, sans-serif"
        }
    }
    pio.templates["corporate_blue"]["layout"]["plot_bgcolor"] = "#FFFFFF"
    pio.templates["corporate_blue"]["layout"]["paper_bgcolor"] = "#FFFFFF"
    pio.templates["corporate_blue"]["layout"]["legend"] = {
        "bgcolor": "rgba(0,0,0,0)",
        "bordercolor": "#E0E0E0",
        "borderwidth": 1
    }

    pio.templates.default = "corporate_blue"

    #Ciemny motyw
    corporate_dark_palette = [
        "#74C0FC", "#2A9D8F", "#A8DADC", "#FFD166", "#EF476F", "#BFD7EA", "#F1FAFB"
    ]

    pio.templates["corporate_dark"] = pio.templates["plotly_dark"]
    pio.templates["corporate_dark"]["layout"]["colorway"] = corporate_dark_palette
    pio.templates["corporate_dark"]["layout"]["font"] = {
        "family": "Segoe UI, Open Sans, sans-serif",
        "size": 15,
        "color": "#f1f1f1"
    }
    pio.templates["corporate_dark"]["layout"]["title"] = {
        "x": 0.05,
        "xanchor": "left",
        "font": {
            "size": 20,
            "color": "#74C0FC",
            "family": "Segoe UI Semibold, sans-serif"
        }
    }
    pio.templates["corporate_dark"]["layout"]["plot_bgcolor"] = "#1e1e1e"
    pio.templates["corporate_dark"]["layout"]["paper_bgcolor"] = "#1e1e1e"
    pio.templates["corporate_dark"]["layout"]["legend"] = {
        "bgcolor": "rgba(0,0,0,0)",
        "bordercolor": "#444",
        "borderwidth": 1
    }
