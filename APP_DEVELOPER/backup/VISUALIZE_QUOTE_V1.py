#pyinstaller --onefile --noconsole VISUALIZE_TOOL.py
#npx electron-packager . VISUALIZE_TOOL --platform=win32 --arch=x64 --out=dist --overwrite

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import sqlite3
import FIND_ORDER
import plotly.express as px

app = dash.Dash(__name__)

# App layout with centered styling
app.layout = html.Div([
    # Background container for the icon
    html.Div([
        html.Img(
            src='https://cryptologos.cc/logos/cardano-ada-logo.png',  # Replace with your icon URL
            style={
                "position": "absolute",
                "top": "50%",
                "left": "50%",
                "transform": "translate(-50%, -50%)",  # Center the icon
                "width": "300px",  # Size of the icon
                "opacity": "0.4",  # Transparency to avoid distraction
                "pointerEvents": "none",  # Prevent interactions with the icon
            }
        ),
    ], style={
        "position": "absolute",  # Ensure this is behind all other content
        "top": 0,
        "left": 0,
        "width": "100%",
        "height": "100%",
        "zIndex": 1,  # Background layer
    }),

    # Main content container
    html.Div([
        html.H1("Product Search Tool", style={"textAlign": "center", "marginBottom": "40px"}),

        html.Div([
            html.Label("Enter Quotation:", style={"fontSize": "20px"}),
            dcc.Input(
                id='quotation-input',
                type='text',
                placeholder="Enter quotation number...",
                style={"margin": "10px auto", "display": "block", "textAlign": "center", "padding": "10px"}
            ),
            html.Button("Search", id='search-button', n_clicks=0,
                        style={"display": "block", "margin": "10px auto", "padding": "10px 20px",
                               "fontSize": "16px", "cursor": "pointer"}),
        ], style={"textAlign": "center"}),  # Center input and button components

        # Output div for search results
        html.Div(id='quotation-output', style={"marginTop": "20px", "textAlign": "center"}),

        # Histogram chart
        dcc.Graph(id='order-histogram', style={"marginTop": "40px", "display": "none"}),

    ], style={
        "position": "relative",
        "zIndex": 2,  # Ensure content appears above the background
        "padding": "20px",
    })
], style={
    "position": "relative",
    "height": "100vh",
    #"background": "linear-gradient(135deg, #ff7e5f, #feb47b)",  # Background gradient
    "overflow": "hidden"  # Prevent scrollbars
})





# Callback to update results and show histogram if SC Code is valid
@app.callback(
    [Output('quotation-output', 'children'),
     Output('order-histogram', 'figure'),
     Output('order-histogram', 'style')],
    [Input('search-button', 'n_clicks')],
    [State('quotation-input', 'value')]
)
def fetch_quotation_data(n_clicks, quotation_number):
    if n_clicks == 0 or not quotation_number:
        return "Please enter a valid quotation number.", {}, {"display": "none"}

    try:
        quotation_number = quotation_number.strip("'")
        ORDER = FIND_ORDER.FETCH_DATA()
        QUOTE = FIND_ORDER.SEARCH_THROUGH_RFQ(quotation_number)
        order_accept_rate_w, order_accept_rate_i = 0, 0

        # Simulate fetching results
        result = FIND_ORDER.CONCAT_QUOTE_ORDER(QUOTE, ORDER)
        if result and len(result) == 5:
            order_accept_rate_w, order_accept_rate_i, sc_code, order_weight, df_show = result

        if sc_code is None:
            return html.H3("This quotation is invalid", style={'color': 'red'}), {}, {"display": "none"}

        # Prepare histogram data (simulate received items for example purposes)
        # Replace this block with your actual data fetching logic
        bar_figure = {
                'data': [
                    {
                        'x': df_show['PRODUCT_CODE'], 
                        'y': df_show['QUANTITY'], 
                        'type': 'bar', 
                        'name': 'Quantity', 
                        'marker': {'color': 'rgba(135, 206, 250, 0.6)'}
                    },
                    {
                        'x': df_show['PRODUCT_CODE'], 
                        'y': df_show['ORDER_QTY'], 
                        'type': 'bar', 
                        'name': 'Order Quantity', 
                        'marker': {'color': 'orange'}
                    }
                ],
                'layout': {
                    'title': 'Quantity vs Order Quantity by Product',
                    'xaxis':dict(
                            title='Product Name',
                            titlefont=dict(size=16),
                            tickangle=45,  # Rotate product names
                            automargin=True,  # Ensure labels are not cut off
                            tickfont=dict(size=10),  # Adjust font size for readability
                        ),
                    'yaxis': {'title': 'Mpcs', 'titlefont' : dict(sixe = 16)},
                    'margin' : dict(l=50, r=50, t=50, b=100),
                    'legend' : dict( x=0.8, y=1.1,  # Position the legend above the chart
                                    orientation="h",  # Horizontal legend
                                    ),
                    'barmode': 'group'  # Bars side-by-side; use 'stack' for overlapping

                }
            }
        # Format results
        order_accept_rate_w_percent = f"{order_accept_rate_w * 100:.2f}%"
        order_accept_rate_i_percent = f"{order_accept_rate_i * 100:.2f}%"
        order_weight_show = f"{order_weight:.2f}"

        return (
            html.Div([
                html.H3(f"Results for Quotation Number: {quotation_number}", style={'color': 'blue', 'marginRight': '20px'}),
                html.P(f"Order Accept Rate (W): {order_accept_rate_w_percent}", style={'marginRight': '20px'}),
                html.P(f"Order Accept Rate (I): {order_accept_rate_i_percent}", style={'marginRight': '20px'}),
                html.P(f"Order Weight: {order_weight_show} kgs", style={'marginRight': '20px'}),
                html.P(f"SC Code: {sc_code}", style={'marginRight': '20px'})
            ], style={"display": "flex", "alignItems": "center", "marginTop": "20px"}),  # First return value
            bar_figure,      # Second return value
            {"display": "block"}  # Third return value
        )


    except Exception as e:
        return f"Error processing quotation: {e}", {}, {"display": "none"}


if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8052)
