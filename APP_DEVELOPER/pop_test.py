import dash
from dash import html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    # Modal for entering exchange rate
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Enter Exchange Rate")),
        dbc.ModalBody([
            html.Label("Exchange Rate:"),
            dcc.Input(id="exchange_rate_input", type="number", value=34.5, step=0.1),
        ]),
        dbc.ModalFooter([
            dbc.Button("Submit", id="submit_exchange_rate", className="ms-auto", n_clicks=0),
            dbc.Button("Close", id="close_modal", className="ms-auto", n_clicks=0),
        ]),
    ], id="exchange_rate_modal", is_open=False),
    
    # Export buttons
    html.Button("Order List Export", id="order_list_export_button", n_clicks=0),
    html.Button("PM DEL Export", id="PM_DEL_export_button", n_clicks=0),
    html.Button("Mark Export", id="Mark_export_button", n_clicks=0),
    
    # Input for file address
    dcc.Input(id="address_column_export_value", type="text", placeholder="Enter file address"),
    
    # Output div
    html.Div(id="address_column_export_output")
])

# Callback to toggle the modal
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
def toggle_modal(n_order, n_submit, n_close, is_open):
    return not is_open

# Callback to generate the sheet
@app.callback(
    Output("address_column_export_output", "children"),
    [
        Input("submit_exchange_rate", "n_clicks"),
        Input("PM_DEL_export_button", "n_clicks"),
        Input("Mark_export_button", "n_clicks"),
    ],
    [
        State("exchange_rate_input", "value"),
        State("address_column_export_value", "value"),
    ],
    prevent_initial_call=True
)
def generate_sheet(n_submit, n_pm_del, n_mark, exchange_rate, file_address):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "submit_exchange_rate" and n_submit:
        try:
            if not file_address:
                return html.Div("Error: File address is required", style={"color": "red"})
            if exchange_rate is None or exchange_rate <= 0:
                return html.Div("Error: Invalid exchange rate", style={"color": "red"})
            # Replace with your actual ORDER_COST_EXPORT_CLS implementation
            # generator = ORDER_COST_EXPORT_CLS(file_address, exchange_rate)
            return html.Div(f"Check file address: {file_address}, Exchange Rate: {exchange_rate}")
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={"color": "red"})

    elif button_id == "PM_DEL_export_button" and n_pm_del:
        try:
            if not file_address:
                return html.Div("Error: File address is required", style={"color": "red"})
            generator = PM_LIST_EXPORT(file_address)
            output = [
                html.P(f"SC Number: {generator.SC_Number}"),
                html.P(f"Order Number: {generator.Order_Number}"),
                html.P(f"Customer Code: {generator.Customer_Code}"),
            ]
            return html.Div(output)
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={"color": "red"})

    elif button_id == "Mark_export_button" and n_mark:
        try:
            if not file_address:
                return html.Div("Error: File address is required", style={"color": "red"})
            generator = MARK_SHEET_EXPORT(file_address)
            if generator.New_Item.empty:
                return html.Div("無初次下單 不需麥頭", style={"color": "green"})
            else:
                output = [
                    html.P(f"SC Number: {generator.SC_Number}"),
                    html.P(f"Order Number: {generator.Order_Number}")
                ]
                return html.Div(output)
        except Exception as e:
            return html.Div(f"Error: {str(e)}", style={"color": "red"})

    return ""

if __name__ == "__main__":
    app.run(debug=True,  
            dev_tools_hot_reload=True, 
            host = "127.0.0.1", 
            port = 8080)
