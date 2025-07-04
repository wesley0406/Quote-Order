import dash
from dash import dcc, html, no_update, page_container, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go  # Added for Figure
import sqlite3
import TRACK_TOOL_V2 as TT 
import plotly.express as px
import sys, os, json
import traceback
import dash.exceptions
from collections import deque
from layout import create_layout  # Import the layout
import blank_page
from flask import Flask, jsonify, Blueprint,request
import dash_bootstrap_components as dbc

# import function from the file
sys.path.append(r"C:\Users\wesley\Desktop\workboard\APP_DEVELOPER\EXTRA_FUNCTION")
from LABEL_DOWNLOAD import ReyherAutomation
from D092_VOLUMN_CHCECK import NN_CHECKVOLUMN
from CARBON_TRACK_FUNC import CO2_Calculator 
from D092_Cement_Screw_Chart_V2 import NN_SCREW_WATER_LEVEL
from ORDER_COST_EXPORT import ORDER_COST_EXPORT_CLS
from PM_DEL_CHECK_EXPORT import PM_LIST_EXPORT
from MARK_EXPORT import MARK_SHEET_EXPORT


#Please run this app fisrt which will generate a website address, then open another terminal then enter ex : "ngrok http --url=sp24437778.ngrok.io 8069 "

# Create Flask app
server = Flask(__name__)

# Define carbon emission tracking  API
api_CO2_VERIFY_blueprint = Blueprint('CO2_TRACK_CALCULATOR', __name__)
@api_CO2_VERIFY_blueprint.route('/CARBON_TRACK', methods=['GET'])
def CARBON_CALCULATOR() :
    TARCK_RECORD = {}
    REVIEW_CO2_EMISSION = pd.DataFrame(columns = ["ORDER_NUMBER", "DISTANCE", "CO2 TONS/KM"])

    #Define the root directory where your files are located
    root_directory = r"Z:\\跨部門\\共用資料夾\\F. 管理部\\05.碳盤查資訊與資料\\2025年度碳盤資料\\活動數據\\類別三\\外車司機\\2025_CARTRACK_SUMMARY\\2025_CAR_TRACK" # please redefine your own root or file 
    #ith open(f'TRACK_LOG.txt', 'w') as log_file:  # 'w' mode clears the file
        #log_file.write("Starting new log!\n")
    CALCULATOR = CO2_Calculator()
    for root, dirs, files in os.walk(root_directory):
        n = 0 
        for i in files :    
            order, dis, co2 , track_dic = CALCULATOR.TRANS_ORDER_INTO_CO2(os.path.join(root_directory,i)) # 丟入欲計算的派車單進root_directory資料夾
            TARCK_RECORD[f"{i.split('.')[0]}"] = track_dic
            print(track_dic)
            #print(os.path.join(root_directory, i))
            REVIEW_CO2_EMISSION.loc[n] = [order.split("\\")[1], dis , co2]
            n += 1
    summary_address_for_dataframe = r"Z:\跨部門\共用資料夾\F. 管理部\05.碳盤查資訊與資料\2025年度碳盤資料\活動數據\類別三\外車司機\2025_CARTRACK_SUMMARY\SUMMARY_2025.xlsx"
    REVIEW_CO2_EMISSION.to_excel(summary_address_for_dataframe)
    #return jsonify({key: list(value.values()) for key, value in TARCK_RECORD.items()})
    return jsonify(TARCK_RECORD)

# Register Blueprint with Flask
server.register_blueprint(api_CO2_VERIFY_blueprint)


app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True, server = server, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
                html.Div(f"Results for Product Code : {app.product_codes[app.current_graph_index]}",
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
                        'x': result['PRODUCT_CODE'].astype(str),
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
           
            bar_figure = go.Figure()
            bar_figure.add_trace(
                go.Bar(
                    x=result['QUOTE_DATE'],
                    y=result['QUANTITY'],
                    name='Quantity',
                    marker_color='rgba(135, 206, 250, 0.6)',
                    marker_line_color='rgba(135, 206, 250, 0.6)',
                    marker_line_width = 2,
                    customdata=result[["WIRE_PRICE", "PROFIT_RATE", "EXCHANGE_RATE"]].to_numpy(),
                    hovertemplate=(
                        "Date: %{x}<br>"
                        "Quantity: %{y}M<br>"
                        "Wire Price: %{customdata[0]}<br>"
                        "Profit: %{customdata[1]}<br>"
                        "Exchange rate: %{customdata[2]}"
                    )
                )
            )
            bar_figure.add_trace(
                go.Bar(
                    x=order_info['CREA_DATE'],
                    y=order_info['ORDER_QTY'],
                    name='Order Quantity',
                    marker_line_color='orange',
                    marker_color='orange',
                    marker_line_width = 2,
                    customdata=order_info[["PRICE", "SC_NO", "CREA_DATE"]].to_numpy(),
                    hovertemplate=(
                        "Order Quantity: %{y}M<br>"
                        "SC: %{customdata[1]}<br>"
                        "Order Price: %{customdata[0]}<br>"
                        "Order Date: %{customdata[2]}<br>"
                    )
                )
            )
            bar_figure.add_trace(
                go.Scatter(
                    x=result['QUOTE_DATE'],
                    y=result['TOTAL_PRICE_M'],
                    name='Quote Price',
                    mode='lines+markers',
                    yaxis='y2',
                    line=dict(color='#d81313', width=2, dash='solid'),
                    marker=dict(size=8, symbol='circle', color='#d81313'),
                    hovertemplate="Quote Price: %{y:.2f}"
                )
            )
            bar_figure.update_layout(
                title=dict(text = wrapped_description, x = 0.5, xanchor='center'),  
                xaxis=dict(title='Quote Date'),
                yaxis=dict(title='Quantity'),
                yaxis2=dict(
                    title='Price',
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    color='#d81313'
                ),
                barmode='group',
                transition_duration=500,
                transition_easing='cubic-in-out',
                showlegend=True,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                ),
                template='plotly_white',
                margin=dict(t=100)
            )
            
            # Store the graph and product code separately
            app.graphs.append(bar_figure)  # Store only the graph data
            app.product_codes.append(product_code)  # Store the product code separately
            app.current_graph_index = len(app.graphs) - 1
            
            # Update button visibility
            prev_style = {'display': 'inline-block'} if app.current_graph_index > 0 else {'display': 'none'}
            next_style = {'display': 'inline-block'} if app.current_graph_index < len(app.graphs) - 1 else {'display': 'none'}
            
            return (
                html.Div([
                    html.Div(f"Results for Product Code : {product_code}", 
                            className = "quotation-title"),
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

# # Add new callback for database update/ temporaly close since this function didn't used frequently
# @app.callback(
#     Output('update-status', 'children'),
#     Input('update-db-button', 'n_clicks'),
#     State('file-path-input', 'value')
# )
# def update_database(n_clicks, file_path):
#     if n_clicks == 0 or not file_path:
#         return ""
    
#     try:
#         TT.UPDATEDB_BYFILE(file_path)
#         return html.Div("Database updated successfully!", 
#                     className="success-message")
#     except Exception as e:
#         return html.Div(f"Error updating database: {str(e)}",
#                     className="error-message")

# Update the callback to only handle clear graphs
@app.callback(
    Output('_', 'children', allow_duplicate=True),
    Input('clear-graphs-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_navigation(clear_clicks):
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
        return html.Div("Error: SC Number is missing!", className="download-status error")

    try:
        bot = ReyherAutomation()
        bot.ORDER_NUM = sc_number.strip()

        print("[DEBUG] Starting login process...")  # Debugging
        if bot.login_download():
            print("[DEBUG] Login successful. Transferring files...")  # Debugging
            bot.TRANSFER_LABEL_FILE()
            return html.Div(
                [
                    "Labels are downloaded and transferred successfully!",
                    html.Br(),
                    f"Root Directory: {bot.destination}"
                ],
                className="download-status success"
            )
        else:
            print("[DEBUG] Login failed.")  # Debugging
            return html.Div("Failed to download labels. Please check your SC number.", className = "download-status error")

    except Exception as e:
        print(f"[DEBUG] Error in downloading: {e}")  # Debugging
        return html.Div(f"Error: {str(e)}", className = "download-status error")

# D092 volumn check system
@app.callback(
    Output('D092_volumn_output', 'children'),
    Input('D092-CBM-button', 'n_clicks'),
    State('D092-sc-input', 'value'),
    prevent_initial_call=True
)
def verify_volume_order(n_clicks, sc_num):
    print(f"SC Number received: {sc_num}")

    if not sc_num:
        return ""
    try:
        # Initialize NN_CHECKVOLUMN
        nn_check_volume = NN_CHECKVOLUMN()
        
        # Set the order number
        nn_check_volume.ORDER_NUM = sc_num
        nn_check_volume._initialize_data()

        weight_modified_list = [1.1, 1.05, 1, 0.95, 0.9]
        # Call the method to verify volume
        volume_summary = nn_check_volume.ORDER_WEI_SUMMERIZED()  # return a dataframe from the ERP system
        summerized_volumn = volume_summary[["item_code", "carton_qty", "inner_box_qty", "pallet_qty","total_package_weight", "screw_weight"]].round(2)
        summerized_volumn = summerized_volumn.reset_index() # add the index into the table 
        adjusted_weight_list = [(i * nn_check_volume.TOTAL_WEIGHT).round(2) for i in weight_modified_list ]
        weight_change_df = pd.DataFrame({
                "Amplifier" : ["+10%", "+5%", "0%", "-5%", "-10%"],
                "Weight(kgs)" : adjusted_weight_list
        })
        return html.Div([
                    dash_table.DataTable(
                        columns = [{"name": col, "id": col} for col in summerized_volumn],
                        data = summerized_volumn.to_dict("records"),
                        style_table = {'overflowX': 'auto'},
                        style_cell = {'textAlign': 'center', 'padding': '5px'},
                        style_header = {'backgroundColor': 'lightgrey', 'fontWeight': 'bold', 'fontSize': '15px'}
                    ),
                    html.Div([
                        html.P("TOTAL WEIGHT FOR SCREW : {} kgs \n".format(summerized_volumn["screw_weight"].sum().round(2))),
                        html.P("TOTAL WEIGHT FOR PACKACGE : {} kgs\n".format(summerized_volumn["total_package_weight"].sum().round(2))),
                        html.P("Over All Weight For The Container : {} kgs\n".format(nn_check_volume.TOTAL_WEIGHT.round(2))),
                        html.P("Pallets quantity for 3 layer pillar : {} \n".format(nn_check_volume.TRIPLE_PALLETS )),
                        html.P("Pallets quantity for 2 layer pillar : {} \n".format(nn_check_volume.DOUBLE_PALLETS )),
                        # add a spce between 2 block 

                        dash_table.DataTable(
                            columns = [{"name": col, "id": col} for col in weight_change_df],
                            data = weight_change_df.to_dict("records"),
                            style_table = {'overflowX': 'auto', 'margin-top': '10px', 'width': '100%', 'margin-bottom': '10px'},
                            style_cell = {'textAlign': 'center', 'padding': '5px'},
                            style_header = {'backgroundColor': 'lightgrey', 'fontWeight': 'bold', 'fontSize': '15px'},
                        ),
                        #add a spce for the result to show
                        html.Div([
                                html.P("Remain Pillar for 40 feet container: {:.2f}".format(
                                    20 - nn_check_volume.TRIPLE_PALLETS / 3 - nn_check_volume.DOUBLE_PALLETS / 2
                                ), style={"flex": "1"}),
                                html.P("Remain Pillar for 20 feet container: {:.2f}".format(
                                    10 - nn_check_volume.TRIPLE_PALLETS / 3 - nn_check_volume.DOUBLE_PALLETS / 2
                                ), style={"flex": "1"})
                            ], id="fill_blank")

                    ], id = "weight_info")
                ], className = "VERIFY_RESULT_container")
    except Exception as e:
        return html.Div(
            f"Error: {str(e)}", 
            className = "verify error"
        )

# D092 cement board screw volumn check system cement board statistic chart
@app.callback(
    Output('quotation-output', 'children', allow_duplicate=True),
    Input('cement_statistic_button', 'n_clicks'),
    prevent_initial_call=True
)
def Cement_Chart(n_clicks):
    bot = NN_SCREW_WATER_LEVEL()
    fig = bot.DRAW_CHART()
    return dcc.Graph(id="main-chart", figure=fig, style={"width": "100%", "height": "700px"})


# popup window module
@app.callback(
    Output("exchange_rate_modal", "is_open"),
    [
        Input("order_list_export_button", "n_clicks"),
        Input("submit_exchange_rate", "n_clicks"),
        Input("close_modal", "n_clicks"),
    ],
    [State("exchange_rate_modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(n_open, n_submit, n_close, is_open):
    return not is_open


# Callback to toggle the notification modal and update its content
@app.callback(
    [
        Output("notification_modal", "is_open"),
        Output("notification_modal_title", "children"),
        Output("notification_modal_body", "children"),
        Output("address_column_export_output", "children")
    ],
    [
        Input("submit_exchange_rate", "n_clicks"),
        Input("PM_DEL_export_button", "n_clicks"),
        Input("Mark_export_button", "n_clicks"),
        Input("close_notification_modal", "n_clicks")
    ],
    [
        State("exchange_rate_input", "value"),
        State("address_column_export_value", "value"),
        State("notification_modal", "is_open")
    ],
    prevent_initial_call=True
)
def generate_sheet(n_submit, n_pm_del, n_mark, n_close_notification, exchange_rate, file_address, notification_modal_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", "", ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Close notification modal if close button is clicked
    if button_id == "close_notification_modal":
        return False, "", "", dash.no_update

    # Initialize outputs
    modal_is_open = False
    modal_title = ""
    modal_body = ""
    output_content = ""

    if button_id == "submit_exchange_rate" and n_submit:
        try:
            if not file_address:
                modal_title = "Error"
                modal_body = html.P("File address is required", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
                return True, modal_title, modal_body, ""
            if exchange_rate is None or exchange_rate <= 0:
                modal_title = "Error"
                modal_body = html.P("Invalid exchange rate", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
                return True, modal_title, modal_body, ""
            # Replace with your actual ORDER_COST_EXPORT_CLS implementation
            generator = ORDER_COST_EXPORT_CLS(file_address, exchange_rate)
            modal_title = "Success"
            modal_body = html.P(f"Check file address: {file_address}, Exchange Rate: {exchange_rate}", style={"color": "green", "fontSize": "20px", "margin": 0})
            return True, modal_title, modal_body, ""
        except Exception as e:
            modal_title = "Error"
            modal_body = html.P(f"Error: {str(e)}", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
            return True, modal_title, modal_body, ""

    elif button_id == "PM_DEL_export_button" and n_pm_del:
        try:
            if not file_address:
                modal_title = "Error"
                modal_body = html.P("File address is required", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
                return True, modal_title, modal_body, ""
            generator = PM_LIST_EXPORT(file_address)
            modal_title = "Success"
            modal_body = html.Div([
                html.P(f"SC Number: {generator.SC_Number}", style={"color": "green", "fontSize": "20px", "margin": 0}),
                html.P(f"Order Number: {generator.Order_Number}", style={"color": "green", "fontSize": "20px", "margin": 0}),
                html.P(f"Customer Code: {generator.Customer_Code}", style={"color": "green", "fontSize": "20px", "margin": 0}),
            ], style={"textAlign": "center"})
            return True, modal_title, modal_body, ""
        except Exception as e:
            modal_title = "Error"
            modal_body = html.P(f"Error: {str(e)}", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
            return True, modal_title, modal_body, ""

    elif button_id == "Mark_export_button" and n_mark:
        try:
            if not file_address:
                modal_title = "Error"
                modal_body = html.P("File address is required", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
                return True, modal_title, modal_body, ""
            generator = MARK_SHEET_EXPORT(file_address)
            modal_title = "Success"
            if generator.New_Item.empty:
                modal_body = html.P("無初次下單 不需麥頭", style={"color": "green", "fontSize": "20px", "margin": 0})
            else:
                modal_body = html.Div([
                    html.P(f"SC Number: {generator.SC_Number}", style={"color": "green", "fontSize": "20px", "margin": 0}),
                    html.P(f"Order Number: {generator.Order_Number}", style={"color": "green", "fontSize": "20px", "margin": 0})
                ], style={"textAlign": "center"})
            return True, modal_title, modal_body, ""
        except Exception as e:
            modal_title = "Error"
            modal_body = html.P(f"Error: {str(e)}", style={"color": "red", "fontSize": "35px", "fontWeight": "bold", "margin": 0})
            return True, modal_title, modal_body, ""

    return modal_is_open, modal_title, modal_body, output_content


# line bot auto sent


if __name__ == "__main__":
    app.run(debug=True,  
            dev_tools_hot_reload=True, 
            host = "127.0.0.1", 
            port = 8069)


