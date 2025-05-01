import pandas as pd
# from mlxtend.frequent_patterns import apriori, association_rules
# from mlxtend.preprocessing import TransactionEncoder
import plotly.express as px
import plotly.io as pio
import holidays
import datetime
import plotly.graph_objects as go

def format_metric_value(value, suffix=""):
    if value >= 1_000_000:
        formatted = f"{value / 1_000_000:.1f} mln"
    elif value >= 100_000:
        formatted = f"{round(value / 1_000):,.0f} tys."
    elif value >= 1_000:
        formatted = f"{value / 1_000:.1f} tys"
    elif value < 100:
        formatted = f"{value:,.2f}"
    else:
        formatted = f"{int(value):,}"
    return formatted + suffix


def get_free_days(start_date, end_date):
    pl_holidays = holidays.Poland(years=range(start_date.year, end_date.year + 1))
    date_range = pd.date_range(start=start_date, end=end_date)
    return [date for date in date_range if date.weekday() >= 5 or date in pl_holidays]


def get_last_day():
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_month = first_day_this_month - datetime.timedelta(days=1)
    first_day_last_month = last_month.replace(day=1)
    return first_day_last_month