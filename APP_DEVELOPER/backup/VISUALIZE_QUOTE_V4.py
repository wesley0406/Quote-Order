import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import sqlite3
import FIND_ORDER
import plotly.express as px
import sys, os
import traceback


#Please run this app fisrt which will generate a website address, then open another terminal then enter ex : "ngrok http http://127.0.0.1:8052 "

app = dash.Dash(__name__)
# Modify the layout to add another input field for the product code
app.layout = html.Div([
    
    html.H1("Quote Analyze Tool", 
                style={
                    "textAlign": "center",
                     "marginBottom": "48px",
                     "fontSize":"64px",
                     "fontFamily":"Arial"
                }
            ),
    html.Div([
        # Quotation input block
        html.Div([
            html.Label("Enter Quotation:", 
                style={
                    "fontSize": "20px", 
                    "display": "block", 
                    "color": "#000",# White text for better visibility
                    "fontWeight":"bold",    
                    "fontFamily":"Arial"
                }
            ),
            dcc.Input(
                id='quotation-input',
                type='text',
                placeholder="Enter quotation number...",
                style={
                    "padding": "10px",
                    "width": "200px",
                    "backgroundColor": "#000",
                    "color": "#FFFFFF",
                    "border": "2px solid #24d19d",
                    "borderRadius": "5px"
                }
            ),
            html.Button("Search", id='search-button', n_clicks=0,
                        style={
                            "margin": "10px 0px 0px 8px",
                            "padding": "10px 20px",
                            "backgroundColor": "#24d19d",
                            "color": "#000000",
                            "border": "2px solid #24d19d",
                            "borderRadius": "5px",
                            "cursor": "pointer",
                        }
            ),
            # html.ButtonHover(style={"boxsShadow":"2px 8px 8px black"})
    ], style={"marginRight": "48px"}),  # Add space between the two blocks

    # Product code input block
    html.Div([
        html.Label("Enter Product Code:", 
            style={
                "fontSize": "20px", 
                "display": "block", 
                # "marginBottom": "10px", 
                "color": "#000",
                "fontWeight":"bold",
                "fontFamily":"Arial"
            }
        ),
            dcc.Input(
                id='product-code-input',
                type='text',
                placeholder="Enter product code...",
                style={
                    "padding": "10px",
                    "width": "200px",
                    "backgroundColor": "#1E1E2F",
                    "color": "#FFFFFF",
                    "border": "2px solid #24d19d",
                    "borderRadius": "5px",
                }
            ),
            html.Button("Analyze",
                id='product-search-button',
                n_clicks=0,
                style={
                    "margin": "10px 0px 0px 8px",
                    "padding": "10px 20px",
                    "backgroundColor": "#24d19d",
                    "color": "#000000",
                    "border": "2px solid #24d19d",
                    "borderRadius": "5px",
                    "cursor": "pointer",
                    # "boxShadow": "0 0 10px #00FFAA"
                }
            ),
    ])
    ], style={
        "display": "flex",  # Flexbox layout for horizontal alignment
        "justifyContent": "center",  # Center items horizontally
        "alignItems": "center",  # Align items vertically
        "marginBottom": "20px",
        }),

    # Output for quotation results
    html.Div(id='quotation-output', 
            style={
                "marginTop": "20px", 
                "textAlign": "center", 
            }
    ),

    # Graph for results
    dcc.Graph(id='order-histogram', style={
        "marginTop": "40px", 
        "display": "none"
    }),
    ],style={
        "backgroundImage": "url('/assets/3274408.jpg')",  # Adjust the path if necessary
        "backgroundSize": "cover",  # Resize the image to fit the screen
        "backgroundRepeat": "no-repeat",  # Prevent the image from repeating
        "backgroundPosition": "center",  # Center the image
        "height": "100vh",  # Ensure it fills the viewport height
        "width": "100vw",  # Ensure it fills the viewport width
        "overflow": "hidden",  # Prevent scrollbars from appearing
        }
    )

# Modify the callback to handle SC_code=None and add product code logic
@app.callback(
    [Output('quotation-output', 'children'),
     Output('order-histogram', 'figure'),
     Output('order-histogram', 'style')],
    [Input('search-button', 'n_clicks'),
     Input('product-search-button', 'n_clicks')],
    [State('quotation-input', 'value'),
     State('product-code-input', 'value')]
)
def handle_inputs(search_clicks, product_clicks, quotation_number, product_code):
    ctx = dash.callback_context

    # Determine which button triggered the callback
    if not ctx.triggered:
        return "", {}, {"display": "none"}
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Quotation search logic
    if triggered_id == 'search-button':
        if search_clicks == 0 or not quotation_number:
            return "Please enter a valid quotation number.", {}, {"display": "none"}

        try:
            quotation_number = quotation_number.strip("'")
            ORDER = FIND_ORDER.FETCH_DATA()
            QUOTE = FIND_ORDER.SEARCH_THROUGH_RFQ(quotation_number)
            sc_code = None

            # Simulate fetching results
            result = FIND_ORDER.CONCAT_QUOTE_ORDER(QUOTE, ORDER)
            if result and len(result) == 5:
                order_accept_rate_w, order_accept_rate_i, sc_code, order_weight, df_show = result

            if sc_code is None:  # SC_code not found
                return "The quotation didn't receive the order, please check!", {}, {"display": "none"}

            # Prepare graph for SC_code
            df_show["PROFIT_RATE"] = df_show["PROFIT_RATE"].map(lambda x: f"{x * 100:.2f}%")
            bar_figure = {
                'data': [
                    {
                        'x': df_show['PRODUCT_CODE'], 
                        'y': df_show['QUANTITY'], 
                        'type': 'bar', 
                        'name': 'Quantity', 
                        'marker': {'color': 'rgba(135, 206, 250, 0.6)'},
                        'hovertemplate' : (
                            "<b>Quantity:</b> %{y}M<br>"
                            "<b>Wire Price:</b> %{customdata[0]}<br>"
                            "<b>Profit:</b> %{customdata[1]}<br>"
                            "<b>Exchange rate:</b> %{customdata[2]}<extra></extra>"),
                        'customdata' : df_show[["WIRE_PRICE", "PROFIT_RATE", "EXCHANGE_RATE" ]].to_numpy()
                        },
                    {
                        'x': df_show['PRODUCT_CODE'], 
                        'y': df_show['ORDER_QTY'], 
                        'type': 'bar', 
                        'name': 'Order Quantity', 
                        'marker': {'color': 'orange'},
                        'hovertemplate' : (
                             "<b>Order Quantity:</b> %{y}M<br>")     
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
            total_item = len(df_show)
            order_item = df_show["ORDER_WEIG"].notna().sum()

            return (
                html.Div([
                    html.H3(f"Results for Quotation Number: {quotation_number}", style={'color': 'blue', 'marginRight': '20px'}),
                    html.P(f"Order Accept Rate (W): {order_accept_rate_w_percent}", style={'marginRight': '20px'}),
                    html.P(f"Order Weight: {order_weight_show} kgs", style={'marginRight': '20px'}),
                    html.P(f"Order Accept Rate (I): {order_accept_rate_i_percent}", style={'marginRight': '20px'}),
                    html.P(f"Order & Quote Ratio: {order_item}/{total_item} ", style={'marginRight': '20px'}),
                    html.P(f"SC Code: {sc_code}", style={'marginRight': '20px'})
                ], style={"display": "flex", "alignItems": "center", "marginTop": "20px"}),  # First return value
                bar_figure,      # Second return value
                {"display": "block"}  # Third return value
            )

        except Exception as e:
            return f"Error processing quotation: {e}", {}, {"display": "none"}

    # Product code search logic
    elif triggered_id == 'product-search-button':
        if product_clicks == 0 or not product_code:
            return "Please enter a valid product code.", {}, {"display": "none"}

        try:
            ORDER = FIND_ORDER.FETCH_DATA()
            ITEM = FIND_ORDER.SEARCH_THROUGH_ITEM(product_code)
            result = FIND_ORDER.SINGLE_ITEM_RECORD(ITEM, ORDER)
            print(result["QUOTE_DATE"])
            # Insert line breaks for long descriptions
            description = result.at[0, "DESCRIPTION"][4:]
            wrapped_description = "<br>".join(description[i:i+85] for i in range(0, len(description),85))
            result["PROFIT_RATE"] = result["PROFIT_RATE"].map(lambda x: f"{x * 100:.2f}%")

            if result.empty:
                return f"No records found for product code: {product_code}.", {}, {"display": "none"}

            # Graph for product code
            bar_figure = {
                    'data': [
                        {
                            'x': result['QUOTE_DATE'],
                            'y': result['QUANTITY'],
                            'type': 'bar',
                            'name': 'Quantity',
                            'marker': {'color': 'rgba(135, 206, 250, 0.6)'},
                            'hovertemplate': (
                                "<b>Quantity:</b> %{y}M<br>"
                                "<b>Wire Price:</b> %{customdata[0]}<br>"
                                "<b>Profit:</b> %{customdata[1]}<br>"
                                "<b>Exchange rate:</b> %{customdata[2]}<extra></extra>"),
                            'customdata' : result[["WIRE_PRICE", "PROFIT_RATE", "EXCHANGE_RATE" ]].to_numpy()
                            },
                        {
                            'x': result['QUOTE_DATE'], 
                            'y': result['ORDER_QTY'], 
                            'type': 'bar', 
                            'name': 'Order Quantity', 
                            'marker': {'color': 'orange'},
                            'hovertemplate': (
                                "<b>Order Quantity:</b> %{y}M<br>"
                                "<b>Order Price:</b> %{customdata[0]}<br>"
                            ),
                            'customdata': result[["TOTAL_PRICE_M"]].to_numpy()
                        }
                    ],
                    'layout': {
                        'title': f'Analysis for Product Code: {wrapped_description}',
                        'xaxis': {'title': 'Quote Date'},
                        'yaxis': {'title': 'Quantity'},
                        'barmode': 'group'
                    }
                }
            return f"Results for Product Code: {product_code}", bar_figure, {"display": "block"}

        except Exception as e:
            return f"Error processing product code: {e}", {}, {"display": "none"}


if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8066)
