import dash
from dash import dcc, html, no_update, page_container
from dash.dependencies import Input, Output, State
import pandas as pd
import sqlite3
import TRACK_TOOL_V2 as TT 
import plotly.express as px
import sys, os
import traceback
import dash.exceptions
from collections import deque
from layout import create_layout  # Import the layout
import blank_page
import sys
sys.path.append(r"C:\Users\wesley\Desktop\workboard\APP_DEVELOPER\C019_LABEL_PROJECT")
from LABEL_DOWNLOAD import ReyherAutomation
from D092_VOLUMN_CHCECK import NN_CHECKVOLUMN


#Please run this app fisrt which will generate a website address, then open another terminal then enter ex : "ngrok http --url=sp24437778.ngrok.io 8069 "

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

# Register pages
dash.register_page('home', layout = create_layout(), path='/')
dash.register_page('blank', layout = blank_page.layout, path='/blank')

app.graphs = deque(maxlen=10)  # Store up to 10 graphs
app.product_codes = deque(maxlen=10)  # Store corresponding product codes
app.current_graph_index = 0

# Use the imported layout
app.layout = html.Div([
    page_container
])


# Simplified index string without inline CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Quote Analyze Tool</title>
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Combine the callbacks into one
@app.callback(
    [Output('quotation-output', 'children'),
    Output('order-histogram', 'figure'),
    Output('order-histogram', 'style'),
    Output('order-histogram', 'className'),
    Output('prev-graph-button', 'style'),
    Output('next-graph-button', 'style')],
    [Input('search-button', 'n_clicks'),
    Input('product-search-button', 'n_clicks'),
    Input('quotation-input', 'n_submit'),
    Input('product-code-input', 'n_submit'),
    Input('prev-graph-button', 'n_clicks'),
    Input('next-graph-button', 'n_clicks'),
    Input('clear-graphs-button', 'n_clicks')],
    [State('quotation-input', 'value'),
    State('product-code-input', 'value')]
)
def handle_all_inputs(search_clicks, product_clicks, quote_submit, product_submit, 
                    prev_clicks, next_clicks, clear_clicks, quotation_number, product_code):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", {}, {"display": "none"}, "results-graph", {'display': 'none'}, {'display': 'none'}

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle navigation buttons
    if triggered_id in ['prev-graph-button', 'next-graph-button']:
        if triggered_id == 'prev-graph-button' and app.current_graph_index > 0:
            app.current_graph_index -= 1
        elif triggered_id == 'next-graph-button' and app.current_graph_index < len(app.graphs) - 1:
            app.current_graph_index += 1

        # Update button visibility
        prev_style = {'display': 'inline-block'} if app.current_graph_index > 0 else {'display': 'none'}
        next_style = {'display': 'inline-block'} if app.current_graph_index < len(app.graphs) - 1 else {'display': 'none'}

        return (
            html.Div([
                html.Div(f"Results for Product Code: {app.product_codes[app.current_graph_index]}",
                        className="quotation-title"),
                html.Div(f"Graph {app.current_graph_index + 1} of {len(app.graphs)}",
                        className="graph-counter")
            ], className="results-container"),
            app.graphs[app.current_graph_index],
            {"display": "block"},
            "results-graph",
            prev_style,
            next_style
        )

    # Handle search inputs
    if triggered_id in ['search-button', 'quotation-input']:
        search_type = 'quotation'
    elif triggered_id in ['product-search-button', 'product-code-input']:
        search_type = 'product'
    else:
        return "", {}, {"display": "none"}, "results-graph", {'display': 'none'}, {'display': 'none'}

    # Validate inputs
    if search_type == 'quotation' and (not quotation_number or (search_clicks == 0 and quote_submit == 0)):
        return (html.Div("Please enter a valid input.", 
                        className="error-message error-block"), 
                {}, {"display": "none"}, "results-graph",
                {'display': 'none'}, {'display': 'none'})
    elif search_type == 'product' and (not product_code or (product_clicks == 0 and product_submit == 0)):
        return (html.Div("Please enter a valid input.", 
                        className="error-message error-block"), 
                {}, {"display": "none"}, "results-graph",
                {'display': 'none'}, {'display': 'none'})

    # Process searches
    if search_type == 'quotation':
        try:
            quotation_number = quotation_number.strip("'")
            ORDER = TT.FETCH_DATA()
            QUOTE = TT.SEARCH_THROUGH_RFQ(quotation_number)
            
            if QUOTE is None:
                return (html.Div("Please enter a valid quotation number.", 
                        className="error-message error-block"),
                        {}, {"display": "none"}, "results-graph",
                        {'display': 'none'}, {'display': 'none'})

            ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I, SC_CODE, ORDER_WEIGHT, result = TT.CONCAT_QUOTE_ORDER(QUOTE, ORDER)

            # Create results div with statistics in horizontal blocks
            results_div = html.Div([
                html.Div(f"Quotation Number: {quotation_number}",
                        className="quotation-title"),
                html.Div([
                    # Weight Acceptance Rate Block
                    html.Div([
                        html.Div("Weight Acceptance Rate", 
                                className="stat-title"),
                        html.Div(f"{ORDER_ACCPET_RATE_W:.2%}",
                                className="stat-value")
                    ], className="stat-block"),
                    
                    # Item Acceptance Rate Block
                    html.Div([
                        html.Div("Item Acceptance Rate", 
                                className="stat-title"),
                        html.Div(f"{ORDER_ACCPET_RATE_I:.2%}",
                                className="stat-value")
                    ], className="stat-block"),
                    
                    # Total Order Weight Block
                    html.Div([
                        html.Div("Total Order Weight", 
                                className="stat-title"),
                        html.Div(f"{ORDER_WEIGHT:.2f} kg",
                                className="stat-value")
                    ], className="stat-block"),
                    
                    # SC Number Block
                    html.Div([
                        html.Div("SC Number", 
                                className="stat-title"),
                        html.Div(f"{SC_CODE if SC_CODE else 'No Order'}",
                                className="stat-value")
                    ], className="stat-block")
                ], className="stats-container"),
                
                # Add Hello World block here
                html.Div([
                    # Wire Price Block
                    html.Div([
                        html.Div("Wire Price", className="price-title"),
                        html.Div(f"{result['WIRE_PRICE'].unique()[0]:.2f}", className="price-value")
                    ], className="price-block"),
                    
                    # Exchange Rate Block  
                    html.Div([
                        html.Div("Exchange Rate", className="price-title"),
                        html.Div([
                            html.Div([
                                *[
                                    html.Span([
                                        f"{rate:.2f}",
                                        " | " if i < len(result['EXCHANGE_RATE'].unique()) - 1 else None
                                    ]) for i, rate in enumerate(sorted(result['EXCHANGE_RATE'].unique(), reverse=True))
                                ]
                            ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '10px'}, className = "price-value")
                        ])
                    ], className="price-block"),
                    
                    # Profit Rate Block showing all unique values horizontally
                    html.Div([
                        html.Div("Profit Rates", className="price-title"), 
                        html.Div([
                            html.Div([
                                *[
                                    html.Span([
                                        f"{rate:.2%}",
                                        " | " if i < len(result['PROFIT_RATE'].unique()) - 1 else None
                                    ]) for i, rate in enumerate(sorted(result['PROFIT_RATE'].unique(), reverse=True))
                                ]
                            ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '10px'})
                        ], className="price-value")
                    ], className="price-block")
                ], className="price-stats-container")
                ], className="quote-container")

            # Create bar figure for quotation
            bar_figure = {
                'data': [
                    {
                        'x': result['PRODUCT_CODE'],
                        'y': result['QUANTITY'],
                        'type': 'bar',
                        'name': 'Quote Quantity',
                        'marker': {'color': 'rgba(135, 206, 250, 0.6)'},
                        'hovertemplate': (
                            "<b>Product:</b> %{x}<br>"
                            "<b>Quote Quantity:</b> %{y}M<br>"
                            "<b>Weight:</b> %{customdata[0]:.2f}kg<br>"
                            "<b>Wire:</b> %{customdata[1]:.2f}<br>"
                            "<b>EX:</b> %{customdata[2]:.2f}<br>"
                            "<b>Profit:</b> %{customdata[3]:.2%}<br>"
                            "<extra></extra>"),
                        'customdata': result[['WEIGHT', 'WIRE_PRICE', 'EXCHANGE_RATE', 'PROFIT_RATE']].to_numpy()
                    },
                    {
                        'x': result['PRODUCT_CODE'],
                        'y': result['ORDER_QTY'],
                        'type': 'bar',
                        'name': 'Order Quantity',
                        'marker': {'color': 'orange'},
                        'hovertemplate': (
                            "<b>Product:</b> %{x}<br>"
                            "<b>Order Quantity:</b> %{y}M<br>"
                            "<b>Weight:</b> %{customdata[0]:.2f}kg<br>"
                            "<extra></extra>"),
                        'customdata': result[['ORDER_WEIG']].to_numpy()
                    }
                ],
                'layout': {
                    'title': f'Quantity Analysis for Quotation: {quotation_number}',
                    'xaxis': {
                        'title': 'Product Code',
                        'tickangle': 45,
                        'automargin': True
                    },
                    'yaxis': {'title': 'Quantity (M)'},
                    'barmode': 'group',
                    'template': 'plotly_white',
                    'transition_duration': 500,
                    'transition_easing': 'cubic-in-out',
                    'animation_frame': None,
                }
            }

            return (results_div, bar_figure, {"display": "block"}, "results-graph",
                {'display': 'none'}, {'display': 'none'})

        except Exception as e:
            return (html.Div(f"Error processing: {e}",
                            className="error-message error-block"),
                    {}, {"display": "none"}, "results-graph",
                    {'display': 'none'}, {'display': 'none'})
    
    elif search_type == 'product':
        try:
            ORDER = TT.FETCH_DATA()
            ITEM = TT.SEARCH_THROUGH_ITEM(product_code)
            result, order_info = TT.SINGLE_ITEM_RECORD_V2(ITEM, ORDER)
            
            # Insert line breaks for long descriptions
            description = result.at[0, "DESCRIPTION"][3:]
            wrapped_description = "<br>".join(description[i:i+85] for i in range(0, len(description),85))
            result["PROFIT_RATE"] = result["PROFIT_RATE"].map(lambda x: f"{x * 100:.2f}%")

            if result.empty:
                return (html.Div(f"No records found for product code: {product_code}", 
                            style={'color': '#ff0000', 'fontWeight': 'bold'}),
                            {}, {"display": "none"}, "results-graph",
                            {'display': 'none'}, {'display': 'none'})

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
                            "<b>Date:</b> %{x}<br>"
                            "<b>Quantity:</b> %{y}M<br>"
                            "<b>Wire Price:</b> %{customdata[0]}<br>"
                            "<b>Profit:</b> %{customdata[1]}<br>"
                            "<b>Exchange rate:</b> %{customdata[2]}<extra></extra>"),
                        'customdata': result[["WIRE_PRICE", "PROFIT_RATE", "EXCHANGE_RATE"]].to_numpy()
                    },
                    {
                        'x': order_info['CREA_DATE'],
                        'y': order_info['ORDER_QTY'],
                        'type': 'bar',
                        'name': 'Order Quantity',
                        'marker': {'color': 'orange'},
                        'hovertemplate': (
                            "<b>Order Quantity:</b> %{y}M<br>"
                            "<b>SC : </b> %{customdata[1]}<br>"
                            "<b>Order Price:</b> %{customdata[0]}<br>"
                            "<b>Order Date:</b> %{customdata[2]}<br>"
                        ),
                        'customdata': order_info[["PRICE", "SC_NO", "CREA_DATE"]].to_numpy()
                    },
                    {
                        'x': result['QUOTE_DATE'],
                        'y': result['TOTAL_PRICE_M'],
                        'type': 'scatter',
                        'mode': 'lines+markers',
                        'name': 'Quote Price',
                        'yaxis': 'y2',  # Use secondary y-axis
                        'line': {
                            'color': '#d81313',
                            'width': 2,
                            'dash': 'solid'
                        },
                        'marker': {
                            'size': 8,
                            'symbol': 'circle',
                            'color': '#d81313'
                        },
                        'hovertemplate': "<b>Quote Price:</b> %{y:.2f}<extra></extra>"
                    }
                ],
                'layout': {
                    'title': f'Analysis for Product Code: {wrapped_description}',
                    'xaxis': {'title': 'Quote Date'},
                    'yaxis': {'title': 'Quantity'},
                    'yaxis2': {
                        'title': 'Price',
                        'overlaying': 'y',
                        'side': 'right',
                        'showgrid': False ,
                        'color': '#d81313'
                    },
                    'barmode': 'group',
                    'transition_duration': 500,
                    'transition_easing': 'cubic-in-out',
                    'showlegend': True,
                    'legend': {
                        'orientation': 'h',
                        'yanchor': 'bottom',
                        'y': 1.02,
                        'xanchor': 'right',
                        'x': 1
                    }
                }
            }
            
            # Store the graph and product code separately
            app.graphs.append(bar_figure)  # Store only the graph data
            app.product_codes.append(product_code)  # Store the product code separately
            app.current_graph_index = len(app.graphs) - 1
            
            # Update button visibility
            prev_style = {'display': 'inline-block'} if app.current_graph_index > 0 else {'display': 'none'}
            next_style = {'display': 'inline-block'} if app.current_graph_index < len(app.graphs) - 1 else {'display': 'none'}
            
            return (
                html.Div([
                    html.Div(f"Results for Product Code: {product_code}",
                            className="quotation-title"),
                    html.Div(f"Graph {app.current_graph_index + 1} of {len(app.graphs)}",
                            className="graph-counter")
                ], className="results-container"),
                bar_figure,
                {"display": "block"},
                "results-graph",
                {'display': 'inline-block'} if app.current_graph_index > 0 else {'display': 'none'},  # prev button
                {'display': 'inline-block'} if app.current_graph_index < len(app.graphs) - 1 else {'display': 'none'}  # next button
            )

        except Exception as e:
            return (
                html.Div(f"Error processing: {e}",
                        style={'color': '#ff0000', 'fontWeight': 'bold'}),
                {},
                {"display": "none"},
                "results-graph",
                {'display': 'none'},
                {'display': 'none'}
            )

# Add new callback for database update
@app.callback(
    Output('update-status', 'children'),
    Input('update-db-button', 'n_clicks'),
    State('file-path-input', 'value')
)
def update_database(n_clicks, file_path):
    if n_clicks == 0 or not file_path:
        return ""
    
    try:
        TT.UPDATEDB_BYFILE(file_path)
        return html.Div("Database updated successfully!", 
                    className="success-message")
    except Exception as e:
        return html.Div(f"Error updating database: {str(e)}",
                    className="error-message")

# Update the callback to only handle clear graphs
@app.callback(
    Output('_', 'children', allow_duplicate=True),
    Input('clear-graphs-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_navigation(clear_clicks):
    print('give me some res')
    if clear_clicks:
        app.graphs.clear()
        app.product_codes.clear()
        app.current_graph_index = 0
        return dcc.Location(pathname='/', id='clear-redirect')
    return dash.no_update
# ------------------------------------------------------------------------
# Update the home button callback
@app.callback(
    Output('_', 'children', allow_duplicate=True),
    Input('home-button', 'n_clicks'),
    prevent_initial_call=True
)
def return_home(n_clicks):
    if n_clicks and n_clicks > 0:
        # Use dcc.Location to trigger a browser redirect
        return dcc.Location(pathname='/', id='home-redirect')
    return dash.no_update

@app.callback(
    Output('download-status', 'children'),
    Input('C019-download-button', 'n_clicks'),
    State('sc-number-input', 'value'),
    prevent_initial_call=True
)
def handle_label_download(n_clicks, sc_number):

    if not sc_number:
        return html.Div("Error: SC Number is missing!", className="error-message")

    try:
        bot = ReyherAutomation()
        bot.ORDER_NUM = sc_number.strip()

        print("[DEBUG] Starting login process...")  # Debugging
        if bot.login_download():
            print("[DEBUG] Login successful. Transferring files...")  # Debugging
            bot.TRANSFER_LABEL_FILE()
            return html.Div("Labels downloaded and transferred successfully!", className="success-message")
        else:
            print("[DEBUG] Login failed.")  # Debugging
            return html.Div("Failed to download labels. Please check your SC number.", className="error-message")

    except Exception as e:
        print(f"[DEBUG] Error in downloading: {e}")  # Debugging
        return html.Div(f"Error: {str(e)}", className="error-message")

# D092 volumn check system
@app.callback(
    Output('D092_volumn_output', 'children'),  # Ensure this ID exists in your layout
    Input('D092-CBM-button', 'n_clicks'),
    State("D092-sc-input", 'value'),
    prevent_initial_call=True
)
def verify_volume_order(n_clicks, sc_number):

    if not sc_number:
        return ""
    try:
        # Initialize NN_CHECKVOLUMN
        nn_check_volume = NN_CHECKVOLUMN()
        
        # Set the order number
        nn_check_volume.ORDER_NUM = sc_number
        
        # Call the method to verify volume
        volume_summary = nn_check_volume.ORDER_WEI_SUMMERIZED()  # Ensure this method exists
        
        return html.Div(
            f"Volume Summary: {volume_summary}",
            className="download-status success"
        )
        
    except Exception as e:
        return html.Div(
            f"Error: {str(e)}", 
            className="download-status error"
        )




if __name__ == "__main__":
    app.run_server(debug=True,  
                dev_tools_hot_reload=True, 
                host="127.0.0.1", 
                port=8069)


