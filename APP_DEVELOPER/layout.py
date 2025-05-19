from dash import dcc, html

def create_layout():
    return html.Div([
        # Header Section
        html.Div([
            html.Div([]),
            html.H1("Quote Analyze Tool"),
            html.Div([
                html.Button(
                    html.I(className="fas fa-trash-alt"), 
                    id='clear-graphs-button', 
                    n_clicks=0,
                    className="clear-graphs-button"
                ),
                html.Div([
                    dcc.Link(
                        html.Button(
                            html.I(className="fas fa-external-link-alt"),
                            className="extra-tool-link-button",
                        ),
                        href='/blank',
                        # target='_blank',
                        # className="page-link hover-text-container"
                    )
                ]),
                html.Button(
                    html.I(className = "fa-solid fa-square-poll-vertical"), 
                    id = 'cement_statistic_button', 
                    n_clicks = 0
                )  
            ], className="button-container")
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

                #new container check
                # html.Div([
                #     html.Label("Update Database:", className="input-label"),
                #     html.Div([
                #         dcc.Input(
                #             id='file-path-input',
                #             type='text',
                #             placeholder="Enter file path...",
                #             className="input-field file-input",
                #         ),
                #         html.Button("Update DB", 
                #             id='update-db-button', 
                #             n_clicks=0,
                #             className="search-button"
                #         ),
                #         html.Button("Clear Out",
                #             id='clear-button', 
                #             n_clicks=0,
                #             className="search-button"
                #         )
                #     ], className="input-group"),
                # ], className="input-container"),

            ], className="input-row"),

            html.Div(id='update-status', className="status-message-container"),
        ], className="input-section"),

        # Results Section
        html.Div([
            html.Div(id='quotation-output', className="results-text"),
            
            html.Div([
                html.Button(
                    html.I(className="fa-solid fa-arrow-left"), 
                    id='prev-graph-button', 
                    n_clicks=0,
                    className="nav-button",
                    style={'display': 'none'}
                ),
                html.Button(
                    html.I(className="fa-solid fa-arrow-right"), 
                    id='next-graph-button', 
                    n_clicks=0,
                    className="nav-button",
                    style={'display': 'none'}
                ),


            ], className="graph-navigation"),
            
            dcc.Loading(
                id="loading-graph",
                type="cube",
                color="#3498db",
                children=[
                    dcc.Graph(
                        id='order-histogram', 
                        className="results-graph",
                        config={
                            'displayModeBar': True,
                            'scrollZoom': True,
                            'displaylogo': False,
                        }
                    )
                ]
            )
        ], className="results-section"),

        html.Div(id='_'),
        dcc.Store(id='refresh-trigger'),
    ], className="main-container") 