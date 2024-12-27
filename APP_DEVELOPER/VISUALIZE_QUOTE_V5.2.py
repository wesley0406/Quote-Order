import dash
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State
import pandas as pd
import sqlite3
import TRACK_TOOL
import plotly.express as px
import sys, os
import traceback
import dash.exceptions
from collections import deque


#Please run this app fisrt which will generate a website address, then open another terminal then enter ex : "ngrok http http://127.0.0.1:8052 "

app = dash.Dash(__name__)
app.graphs = deque(maxlen=10)  # Store up to 10 graphs
app.product_codes = deque(maxlen=10)  # Store corresponding product codes
app.current_graph_index = 0

# Modify the layout to add another input field for the product code
app.layout = html.Div([
    # Header Section
    html.Div([
        html.H1("Quote Analyze Tool"),
        # Add Clear Graphs button
        html.Button("Clear Graphs", 
            id='clear-graphs-button', 
            n_clicks=0,
            className="clear-graphs-button"
        )
    ], className="header-section"),

    # Input Section with File Update
    html.Div([
        # First row of inputs
        html.Div([
            # Quotation Input Container
            html.Div([
                html.Label("Enter Quotation:", className="input-label"),
                html.Div([
                    dcc.Input(
                        id='quotation-input',
                        type='text',
                        placeholder="Enter quotation number...",
                        className="input-field",
                        n_submit=0
                    ),
                    html.Button("Search", 
                        id='search-button', 
                        n_clicks=0,
                        className="search-button"
                    )
                ], className="input-group")
            ], className="input-container"),

            # Product Code Input Container
            html.Div([
                html.Label("Enter Product Code:", className="input-label"),
                html.Div([
                    dcc.Input(
                        id='product-code-input',
                        type='text',
                        placeholder="Enter product code...",
                        className="input-field",
                        n_submit=0
                    ),
                    html.Button("Analyze",
                        id='product-search-button',
                        n_clicks=0,
                        className="search-button"
                    )
                ], className="input-group")
            ], className="input-container"),
        ], className="input-row"),

        # Second row with file update
        html.Div([
            # File Update Container
            html.Div([
                html.Label("Update Database:", className="input-label"),
                html.Div([
                    dcc.Input(
                        id='file-path-input',
                        type='text',
                        placeholder="Enter file path...",
                        className="input-field file-input",
                    ),
                    html.Button("Update DB", 
                        id='update-db-button', 
                        n_clicks=0,
                        className="search-button"
                    ),
                    html.Button("Clear Out",  # Add the Clear Out button
                        id='clear-button', 
                        n_clicks=0,
                        className="search-button"
                    )
                ], className="input-group"),
            ], className="input-container",
              )
        ], className="input-row"),

        # Status message below the inputs
        html.Div(id='update-status', className="status-message-container"),
    ], className="input-section"),

    # Results Section with Navigation
    html.Div([
        html.Div(id='quotation-output', className="results-text"),
        
        # Add navigation buttons
        html.Div([
            html.Button("Previous", 
                id='prev-graph-button', 
                n_clicks=0,
                className="nav-button",
                style={'display': 'none'}
            ),
            html.Button("Next", 
                id='next-graph-button', 
                n_clicks=0,
                className="nav-button",
                style={'display': 'none'}
            ),
        ], className="graph-navigation"),
        
        # Graph container
        dcc.Graph(id='order-histogram', className="results-graph")
    ], className="results-section")
], className="main-container")

# Simplified index string without inline CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Quote Analyze Tool</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
            <script src="/assets/notifications.js"></script>
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

    # Handle clear graphs button
    if triggered_id == 'clear-graphs-button' and clear_clicks > 0:
        app.graphs.clear()
        app.product_codes.clear()
        app.current_graph_index = 0
        return "", {}, {"display": "none"}, "results-graph", {'display': 'none'}, {'display': 'none'}

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
                        style={'fontSize': '36px'}),
                html.Div(f"Graph {app.current_graph_index + 1} of {len(app.graphs)}",
                        style={'fontSize': '14px', 'color': '#666'})
            ]),
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
                {}, {"display": "none"}, "results-graph fade-out",
                {'display': 'none'}, {'display': 'none'})
    elif search_type == 'product' and (not product_code or (product_clicks == 0 and product_submit == 0)):
        return (html.Div("Please enter a valid input.", 
                        className="error-message error-block"), 
                {}, {"display": "none"}, "results-graph fade-out",
                {'display': 'none'}, {'display': 'none'})

    # Process searches
    if search_type == 'quotation':
        try:
            quotation_number = quotation_number.strip("'")
            ORDER = TRACK_TOOL.FETCH_DATA()
            QUOTE = TRACK_TOOL.SEARCH_THROUGH_RFQ(quotation_number)
            
            if QUOTE is None:
                return (html.Div("Please enter a valid quotation number.", 
                               className="error-message error-block"),
                       {}, {"display": "none"}, "results-graph fade-out",
                       {'display': 'none'}, {'display': 'none'})

            ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I, SC_CODE, ORDER_WEIGHT, result = TRACK_TOOL.CONCAT_QUOTE_ORDER(QUOTE, ORDER)

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
                ], className="stats-container")
            ], className="results-container")

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
                            "<extra></extra>"),
                        'customdata': result[['WEIGHT']].to_numpy()
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
                    'xaxis': {'title': 'Product Code'},
                    'yaxis': {'title': 'Quantity (M)'},
                    'barmode': 'group',
                    'template': 'plotly_white'
                }
            }

            return (results_div, bar_figure, {"display": "block"}, "results-graph",
                   {'display': 'none'}, {'display': 'none'})

        except Exception as e:
            return (html.Div(f"Error processing: {e}",
                            className="error-message error-block"),
                    {}, {"display": "none"}, "results-graph fade-out",
                    {'display': 'none'}, {'display': 'none'})
    
    elif search_type == 'product':
        try:
            ORDER = TRACK_TOOL.FETCH_DATA()
            ITEM = TRACK_TOOL.SEARCH_THROUGH_ITEM(product_code)
            result = TRACK_TOOL.SINGLE_ITEM_RECORD(ITEM, ORDER)
            
            # Insert line breaks for long descriptions
            description = result.at[0, "DESCRIPTION"][4:]
            wrapped_description = "<br>".join(description[i:i+85] for i in range(0, len(description),85))
            result["PROFIT_RATE"] = result["PROFIT_RATE"].map(lambda x: f"{x * 100:.2f}%")

            if result.empty:
                return (html.Div(f"No records found for product code: {product_code}", 
                               style={'color': '#ff0000', 'fontWeight': 'bold'}),
                       {}, {"display": "none"}, "results-graph fade-out",
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
                        'x': result['QUOTE_DATE'],
                        'y': result['ORDER_QTY'],
                        'type': 'bar',
                        'name': 'Order Quantity',
                        'marker': {'color': 'orange'},
                        'hovertemplate': (
                            "<b>Order Quantity:</b> %{y}M<br>"
                            "<b>SC : </b> %{customdata[1]}<br>"
                            "<b>Order Price:</b> %{customdata[0]}<br>"
                        ),
                        'customdata': result[["TOTAL_PRICE_M", "SC_CODE"]].to_numpy()
                    }
                ],
                'layout': {
                    'title': f'Analysis for Product Code: {wrapped_description}',
                    'xaxis': {'title': 'Quote Date'},
                    'yaxis': {'title': 'Quantity'},
                    'barmode': 'group'
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
                prev_style,
                next_style
            )

        except Exception as e:
            return (
                html.Div(f"Error processing: {e}",
                        style={'color': '#ff0000', 'fontWeight': 'bold'}),
                {},
                {"display": "none"},
                "results-graph fade-out",
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
        TRACK_TOOL.UPDATEDB_BYFILE(file_path)
        return html.Div("Database updated successfully!", 
                       style={
                           'color': '#4CAF50',
                           'fontWeight': 'bold', 
                           'fontSize': '24px',
                           'textAlign': 'center',
                           'padding': '20px',
                           'backgroundColor': '#E8F5E9',
                           'borderRadius': '10px',
                           'margin': '20px auto',
                           'maxWidth': '500px',
                           'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                           'border': '2px solid #4CAF50'
                       })
    except Exception as e:
        return html.Div(f"Error updating database: {str(e)}", 
                       style={
                           'color': '#ff0000',
                           'fontWeight': 'bold',
                           'fontSize': '20px',
                           'textAlign': 'center',
                           'padding': '20px',
                           'backgroundColor': '#7d7e80',
                           'borderRadius': '25px',
                           'margin': '20px auto',
                           'maxWidth': '500px'
                       })

# Add new callback for clearing the input
@app.callback(
    Output('file-path-input', 'value'),
    Input('clear-button', 'n_clicks')
)
def clear_input(n_clicks):
    if n_clicks > 0:
        return ""
    return dash.no_update

if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1", port=8069)
