# app.py
import dash
from dash import dcc, html
import pandas as pd
#electron-packager . MyDashApp --platform=win32 --arch=x64 --overwrite

# Fetch data
def fetch_data():
    return pd.DataFrame({
        "x": [1, 2, 3, 4],
        "y": [10, 15, 13, 17]
    })

df = fetch_data()

# Create Dash app
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Dash Desktop App"),
    dcc.Graph(
        id="example-graph",
        figure={
            "data": [{"x": df["x"], "y": df["y"], "type": "line", "name": "Example"}],
            "layout": {"title": "Line Chart"}
        }
    )
])

if __name__ == "__main__":
    app.run_server(debug=True)
