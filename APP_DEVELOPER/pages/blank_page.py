from dash import html, dcc

layout = html.Div([
    # Navigation section
    html.Div([
        dcc.Link(
            html.Button(
                html.I(className="fa-solid fa-house"), 
                id='home-button',
                className="nav-button",
                n_clicks=0
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
                        id='download-button',
                        style={
                            'color': 'white',
                            'padding': '10px 35px',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '25px',
                            'fontWeight': 'bold',
                        }
                    )
                ], style={
                    'display': 'flex',
                    'justify-content': 'space-around',
                    'marginBottom': '10px'  # Space between input row and status
                }),
                # Second row: Status message
                html.Div(id='download-status')
            ], className="label-download-container",
                style={
                'flexDirection': 'column',  # Stack children vertically
                'marginBottom': '50px',
                })
        ])
    ], style={
        'padding': '40px',
        'minHeight': 'calc(100vh - 60px)',
        'backgroundColor': '#f5f5f5'
    })
])