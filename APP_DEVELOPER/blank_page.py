from dash import html, dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    # Navigation section
    html.Div([
        dcc.Link(
            html.Button(
                html.I(className="fa-solid fa-house"), 
                id = 'home-button',
                className = "nav-button",
                n_clicks = 0
            ),
            href='/',
        )
    ], className="nav-section"),
    
    # Main content section
    html.Div([
        html.Div([
            html.Img(
                src='/assets/reyher_logo.png',  # Make sure to add this image to your assets folder
                style={
                    'height': '60px',
                    'verticalAlign': 'middle'
                }
            ),
            html.H2("Label Download", 
                style={
                    'backgroundImage': 'linear-gradient(to right, #FF6B00 60%, #333 40%)',
                    'WebkitBackgroundClip': 'text',
                    'WebkitTextFillColor': 'transparent',# Makes the text transparent to show gradient
                    'marginLeft': '30px',
                    'fontSize': '45px',
                    'fontWeight': 'bold',
                    'display': 'inline-block'
                }),
        ],className = "LABEL_DOWNLOAD_LOGO_PART"),  
        # Input container
        html.Div([
                # First row: Label, Input, and Button
                html.Div([
                    html.Label("Enter SC Number:", 
                        style={
                            'color': '#333',
                            'fontSize': '30px',
                            'fontWeight': 'bold',
                        }),
                    dcc.Input(
                        id='sc-number-input',
                        type='text',
                        debounce=True,
                        value='',  # Ensure it's controlled from the start
                        placeholder="ex : 25020022",
                        style={
                            'width': '600px',
                            'padding': '10px',
                            'border': '1px solid #ccc',
                            'borderRadius': '4px',
                            'fontSize': '16px',
                            'marginBottom': '10px',
                            'borderWidth': '5px',
                            'borderStyle': 'dashed solid',
                            'borderColor': 'black'
                        }
                    ),
                    html.Button(
                        "GO !!!",
                        id = 'C019-download-button',
                        n_clicks = 0,
                        style={
                            'color': 'white',
                            'width': '120px',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '25px',
                            'fontWeight': 'bold',
                        }
                    ),
                    html.Div("", id ="download-status"),
                ], className = "label-download-container"
                )
        ])
    ], style={
        'padding': '5px',
        'height' : '270px',
        'backgroundColor': '#f5f5f5'
        }
    ),
    #D092 volumn calculation contianer
    html.Div([
        html.Div([
            html.Img(
                src='/assets/NN_logo.png',  # Make sure to add this image to your assets folder
                style={
                    'height': '60px',
                    'verticalAlign': 'middle'
                }
            ),
            html.H2("CBM VERIFY", 
                style={
                    'backgroundColor': '#8f8e8c',
                    'WebkitBackgroundClip': 'text',
                    'WebkitTextFillColor': 'transparent',# Makes the text transparent to show gradient
                    'marginLeft': '30px',
                    'fontSize': '45px',
                    'fontWeight': 'bold',
                    'display': 'inline-block'
                }),
        ],className = "LABEL_DOWNLOAD_LOGO_PART"),
        html.Div([
            html.Label("Enter SC Number:", 
                style={
                    'color': '#333',
                    'fontSize': '30px',
                    'fontWeight': 'bold',
                }
            ),
            dcc.Input(
                id = 'D092-sc-input',
                    type = 'text',
                    placeholder = "ex : 250010001",
                    style = {
                        'width': '600px',
                        'padding': '10px',
                        'border': '1px solid #ccc',
                        'borderRadius': '4px',
                        'fontSize': '16px',
                        'marginBottom': '10px',
                        'borderWidth': '5px',
                        'borderStyle': 'dashed solid',
                        'borderColor': 'black'
                    }
            ),
            html.Button(
                "CHECK VOLUMN !!!",
                id ='D092-CBM-button',
                style = {
                    'color': 'white',
                    'padding': '10px 10px',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontSize': '15px',
                    'fontWeight': 'bold',
                    'width': '120px'
                }
            ),
            html.Div("", id = "D092_volumn_output")
        ], className = "label-download-container")
    ], className = "CBM-verify-container"),
    html.Div([
        html.Div([
            html.Img(
                src='/assets/ERP_logo.png',  # Make sure to add this image to your assets folder
                style={
                    'height': '80px',
                    'verticalAlign': 'middle'
                }
            ),
            html.H2("COMPLETE ORDER ", 
                style={
                    'backgroundColor': '#EAC100',
                    'WebkitBackgroundClip': 'text',
                    'WebkitTextFillColor': 'transparent',# Makes the text transparent to show gradient
                    'marginLeft': '30px',
                    'marginTop': '15px',
                    'fontSize': '45px',
                    'fontWeight': 'bold',
                    'display': 'inline-block'
                }),
        ],className = "LABEL_DOWNLOAD_LOGO_PART"),
        html.Div([
            html.Label("Enter File Addresss:", 
                style={
                    'color': '#333',
                    'fontSize': '30px',
                    'fontWeight': 'bold',
                }
            ),
            html.Div(
                dbc.Modal([
                    dbc.ModalHeader(dbc.ModalTitle("Enter Exchange Rate")),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col(
                                html.Label("Exchange Rate:", className="mb-0"),
                                width=4,
                                className="d-flex align-items-center"
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id="exchange_rate_input",
                                    type="number",
                                    value=33,
                                    step=0.01,
                                    className="form-control"
                                ),
                                width=8,
                                className="d-flex align-items-center"
                            ),
                        ], align="center")
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Submit", id="submit_exchange_rate", className="ms-auto", n_clicks=0),
                        dbc.Button("Close", id="close_modal", className="ms-auto", n_clicks=0),
                    ]),
                ], id="exchange_rate_modal", is_open=False)
            ),
            # Output div
            dcc.Input(
                id = 'address_column_export_value',
                    type = 'text',
                    placeholder = r"ex : Z:\業務部\業務一課\H-訂單\1. 外銷\D09000 BMD\1. 訂單\2025\20250327",
                    style = {
                        'width': '600px',
                        'padding': '10px',
                        'border': '1px solid #ccc',
                        'borderRadius': '4px',
                        'fontSize': '16px',
                        'marginBottom': '10px',
                        'borderWidth': '5px',
                        'borderStyle': 'dashed solid',
                        'borderColor': 'black'
                    }
            ),
            html.Button(
                "輸出明細",
                id ='PM_DEL_export_button',
                style = {
                    'color': 'white',
                    'padding': '10px 10px',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontSize': '15px',
                    'fontWeight': 'bold',
                    'width': '150px'
                }
            ),
            html.Button(
                "輸出麥頭",
                id ='Mark_export_button',
                style = {
                    'color': 'white',
                    'padding': '10px 10px',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontSize': '15px',
                    'fontWeight': 'bold',
                    'width': '150px'
                }
            ),
            html.Button(
                "輸出訂單成本表",
                id ='order_list_export_button',
                style = {
                    'color': 'white',
                    'padding': '10px 10px',
                    'border': 'none',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontSize': '15px',
                    'fontWeight': 'bold',
                    'width': '150px'
                }
            ),
            html.Div("", id = "address_column_export_output"),

            # Notification Modal (for both errors and success)
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(id="notification_modal_title")),
                dbc.ModalBody(
                    id="notification_modal_body",
                    className="d-flex justify-content-center align-items-center",
                    style={"minHeight": "100px"}
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close_notification_modal", className="ms-auto", n_clicks=0)
                ),
            ], id="notification_modal", is_open=False)
            ], className = "sheet-container")
    ], className = "sheet_output_continaer", style = {'backgroundcolor': '#D6D6AD'})
])
