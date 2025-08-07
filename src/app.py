"""
Main Dash Application
Cal Men's Club Soccer Administrative Dashboard
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from configs import (
    app_config, Colors, UserRoles, Permissions, 
    NavigationConfig, validate_config
)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="Cal Men's Club Soccer Dashboard"
)

# Custom CSS styling with UC Berkeley colors
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --uc-blue: ''' + Colors.UC_BLUE + ''';
                --uc-gold: ''' + Colors.UC_GOLD + ''';
                --forest-green: ''' + Colors.FOREST_GREEN + ''';
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: ''' + Colors.LIGHT_BACKGROUND + ''';
            }
            
            .navbar-custom {
                background-color: var(--uc-blue) !important;
                border-bottom: 3px solid var(--uc-gold);
            }
            
            .navbar-custom .navbar-brand,
            .navbar-custom .nav-link {
                color: white !important;
            }
            
            .navbar-custom .nav-link:hover {
                color: var(--uc-gold) !important;
                background-color: rgba(253, 181, 21, 0.1);
                border-radius: 4px;
            }
            
            .btn-primary {
                background-color: var(--uc-blue);
                border-color: var(--uc-blue);
            }
            
            .btn-primary:hover {
                background-color: var(--uc-gold);
                border-color: var(--uc-gold);
                color: black;
            }
            
            .card-header {
                background-color: var(--uc-blue);
                color: white;
                border-bottom: 2px solid var(--uc-gold);
            }
            
            .login-container {
                min-height: 100vh;
                background: linear-gradient(135deg, var(--uc-blue) 0%, var(--forest-green) 100%);
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .login-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0, 50, 98, 0.3);
                border-top: 5px solid var(--uc-gold);
            }
            
            .dashboard-stats {
                background: linear-gradient(135deg, var(--uc-gold) 0%, #FFD700 100%);
                color: var(--uc-blue);
                border-radius: 10px;
            }
            
            .attendance-card {
                border-left: 4px solid var(--forest-green);
            }
            
            .payment-card {
                border-left: 4px solid var(--uc-gold);
            }
        </style>
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

# Mock user session (in production, this would come from proper authentication)
current_user_session = {
    'logged_in': False,
    'username': None,
    'role': None,
    'user_id': None,
    'login_time': None
}

def create_navbar(user_role=None):
    """Create navigation bar based on user role"""
    if not user_role:
        return html.Div()  # No navbar for login page
    
    # Get navigation items based on role permissions
    nav_items = []
    
    # Standard navigation items
    for item in NavigationConfig.NAV_ITEMS:
        if Permissions.has_permission(user_role, item['permission']):
            nav_items.append(
                dbc.NavItem(
                    dbc.NavLink(
                        [html.I(className=item['icon']), " ", item['name']],
                        href=item['path'],
                        id=f"nav-{item['name'].lower().replace(' ', '-')}",
                        className="me-3"
                    )
                )
            )
    
    # Executive-only navigation items
    if user_role == UserRoles.EXEC:
        nav_items.append(
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem(
                        [html.I(className=item['icon']), " ", item['name']], 
                        href=item['path']
                    ) for item in NavigationConfig.EXEC_NAV_ITEMS
                ],
                nav=True,
                in_navbar=True,
                label=[html.I(className="fas fa-cog"), " Executive"],
                className="me-3"
            )
        )
    
    # User dropdown
    user_dropdown = dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem("Profile", href="/profile"),
            dbc.DropdownMenuItem("Account Settings", href="/account"),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Logout", href="/logout", id="logout-btn")
        ],
        nav=True,
        in_navbar=True,
        label=[html.I(className="fas fa-user"), f" {current_user_session.get('username', 'User')}"],
        align_end=True
    )
    
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand([
                html.I(className="fas fa-futbol me-2"),
                "Cal Men's Club Soccer"
            ], href="/dashboard"),
            dbc.Nav(nav_items + [user_dropdown], className="ms-auto", navbar=True)
        ]),
        className="navbar-custom",
        dark=True,
        sticky="top"
    )

def create_login_page():
    """Create login page"""
    return html.Div(
        className="login-container",
        children=[
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-futbol fa-3x mb-4", 
                                          style={'color': Colors.UC_BLUE}),
                                    html.H2("Cal Men's Club Soccer", 
                                           className="mb-4", 
                                           style={'color': Colors.UC_BLUE}),
                                    html.P("Please sign in to access your dashboard", 
                                          className="text-muted mb-4"),
                                    
                                    dbc.Form([
                                        dbc.Row([
                                            dbc.Label("Username", html_for="login-username"),
                                            dbc.Input(
                                                id="login-username",
                                                type="text",
                                                placeholder="Enter your username",
                                                className="mb-3"
                                            )
                                        ]),
                                        dbc.Row([
                                            dbc.Label("Password", html_for="login-password"),
                                            dbc.Input(
                                                id="login-password",
                                                type="password",
                                                placeholder="Enter your password",
                                                className="mb-3"
                                            )
                                        ]),
                                        dbc.Row([
                                            dbc.Checkbox(
                                                id="remember-me",
                                                label="Remember me",
                                                className="mb-3"
                                            )
                                        ]),
                                        dbc.Button(
                                            "Sign In",
                                            id="login-btn",
                                            color="primary",
                                            className="w-100 mb-3",
                                            size="lg"
                                        ),
                                        html.Div(id="login-message")
                                    ])
                                ], className="text-center")
                            ])
                        ], className="login-card")
                    ], width=12, md=6, lg=4)
                ], justify="center")
            ])
        ]
    )

def create_dashboard_page(user_role):
    """Create dashboard page based on user role"""
    
    # Stats cards - content varies by role
    if user_role == UserRoles.EXEC:
        stats = [
            {"title": "Total Members", "value": "45", "icon": "fas fa-users", "color": "primary"},
            {"title": "Active Events", "value": "8", "icon": "fas fa-calendar", "color": "success"},
            {"title": "Pending Payments", "value": "$2,450", "icon": "fas fa-dollar-sign", "color": "warning"},
            {"title": "Attendance Rate", "value": "87%", "icon": "fas fa-chart-line", "color": "info"}
        ]
    else:  # Member
        stats = [
            {"title": "My Attendance", "value": "92%", "icon": "fas fa-calendar-check", "color": "success"},
            {"title": "Payment Status", "value": "Paid", "icon": "fas fa-check-circle", "color": "primary"},
            {"title": "Next Event", "value": "Tomorrow", "icon": "fas fa-clock", "color": "warning"},
            {"title": "Events Attended", "value": "23", "icon": "fas fa-futbol", "color": "info"}
        ]
    
    stat_cards = []
    for stat in stats:
        stat_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                html.H4(stat["value"], className="mb-0"),
                                html.P(stat["title"], className="mb-0 text-muted")
                            ], className="col"),
                            html.Div([
                                html.I(className=f"{stat['icon']} fa-2x text-{stat['color']}")
                            ], className="col-auto")
                        ], className="row align-items-center")
                    ])
                ])
            ], width=12, md=6, lg=3, className="mb-4")
        )
    
    return html.Div([
        dbc.Container([
            # Welcome header
            dbc.Row([
                dbc.Col([
                    html.H1(f"Welcome back, {current_user_session.get('username', 'User')}", 
                           className="mb-1"),
                    html.P(f"Role: {user_role.title()} | Last login: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                          className="text-muted mb-4")
                ])
            ]),
            
            # Stats cards
            dbc.Row(stat_cards),
            
            # Main content area
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-chart-bar me-2"),
                            "Recent Activity"
                        ]),
                        dbc.CardBody([
                            html.P("Dashboard content will be implemented here based on user role."),
                            html.P(f"Current role: {user_role}"),
                            html.P("This area will show:"),
                            html.Ul([
                                html.Li("Recent attendance records"),
                                html.Li("Upcoming events"),
                                html.Li("Payment management" if user_role == UserRoles.EXEC else "Payment status"),
                                html.Li("Team announcements"), 
                                html.Li("Member management tools" if user_role == UserRoles.EXEC else "Personal stats")
                            ])
                        ])
                    ])
                ], width=12, lg=8),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-bell me-2"),
                            "Notifications"
                        ]),
                        dbc.CardBody([
                            html.P("No new notifications", className="text-muted")
                        ])
                    ])
                ], width=12, lg=4)
            ], className="mb-4")
        ])
    ])

def create_placeholder_page(page_name, user_role):
    """Create placeholder pages for other sections"""
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(f"{page_name.title()}", className="mb-4"),
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{page_name.title()} Module"),
                            html.P(f"This is the {page_name} section for users with {user_role} role."),
                            html.P("Content will be implemented in future phases."),
                            html.Hr(),
                            html.P("Features planned:"),
                            html.Ul([
                                html.Li(f"{page_name.title()}-specific functionality"),
                                html.Li("Data visualization"),
                                html.Li("Interactive forms"),
                                html.Li("Export capabilities")
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ])

# Main app layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='user-session', data=current_user_session),
    html.Div(id='page-content')
])

# Callbacks for page routing and authentication
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('user-session', 'data')
)
def display_page(pathname, session):
    """Handle page routing based on authentication and permissions"""
    
    # If not logged in, show login page for all routes except login
    if not session.get('logged_in', False):
        return create_login_page()
    
    user_role = session.get('role', UserRoles.MEMBER)
    
    # Create navbar for authenticated users
    navbar = create_navbar(user_role)
    
    # Route to appropriate page
    if pathname == '/dashboard' or pathname == '/':
        if Permissions.has_permission(user_role, 'dashboard'):
            content = create_dashboard_page(user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. You don't have permission to view this page.", color="danger")
            ])
    
    elif pathname == '/attendance':
        if Permissions.has_permission(user_role, 'attendance'):
            content = create_placeholder_page('attendance', user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. You don't have permission to view this page.", color="danger")
            ])
    
    elif pathname == '/payments':
        if Permissions.has_permission(user_role, 'payments'):
            content = create_placeholder_page('payments', user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. You don't have permission to view this page.", color="danger")
            ])
    
    elif pathname == '/settings':
        if Permissions.has_permission(user_role, 'settings'):
            content = create_placeholder_page('settings', user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. You don't have permission to view this page.", color="danger")
            ])
    
    # Executive-only pages
    elif pathname == '/members':
        if Permissions.has_permission(user_role, 'member_management'):
            content = create_placeholder_page('member management', user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. Executive privileges required.", color="danger")
            ])
    
    elif pathname == '/events':
        if Permissions.has_permission(user_role, 'event_management'):
            content = create_placeholder_page('event management', user_role)
        else:
            content = html.Div([
                dbc.Alert("Access denied. Executive privileges required.", color="danger")])

    

    elif pathname == '/reports':

        if Permissions.has_permission(user_role, 'financial_reports'):

            content = create_placeholder_page('financial reports', user_role)

        else:

            content = html.Div([

                dbc.Alert("Access denied. Executive privileges required.", color="danger")
            ])
    
    else:
        content = html.Div([
            dbc.Container([
                dbc.Alert("Page not found", color="warning"),
                html.P("The page you're looking for doesn't exist.")
            ])
        ])
    
    return html.Div([navbar, content])

# Login callback
@app.callback(
    [Output('user-session', 'data'),
     Output('login-message', 'children'),
     Output('url', 'pathname')],
    Input('login-btn', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('user-session', 'data')]
)
def handle_login(n_clicks, username, password, session):
    """Handle login authentication (mock implementation)"""
    if n_clicks is None:
        return session, "", dash.no_update
    
    # Mock authentication - in production, this would verify against database/API
    mock_users = {
        'executive': {'password': 'executive123', 'role': UserRoles.EXEC},
        'member': {'password': 'member123', 'role': UserRoles.MEMBER}
    }
    
    if username in mock_users and password == mock_users[username]['password']:
        # Successful login
        session['logged_in'] = True
        session['username'] = username
        session['role'] = mock_users[username]['role']
        session['user_id'] = f"user_{username}"
        session['login_time'] = datetime.now().isoformat()
        
        return session, "", "/dashboard"
    else:
        # Failed login
        message = dbc.Alert(
            "Invalid username or password. Try: executive/executive123 or member/member123",
            color="danger",
            className="mt-3"
        )
        return session, message, dash.no_update

# Logout callback
@app.callback(
    [Output('user-session', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('logout-btn', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """Handle user logout"""
    if n_clicks:
        # Clear session
        empty_session = {
            'logged_in': False,
            'username': None,
            'role': None,
            'user_id': None,
            'login_time': None
        }
        return empty_session, "/"
    return dash.no_update, dash.no_update

if __name__ == '__main__':
    # Validate configuration before starting
    config_errors = validate_config()
    if config_errors:
        print("Configuration Errors Found:")
        for error in config_errors:
            print(f"  - {error}")
        print("\nPlease check your .env file and fix these issues before running the app.")
    else:
        print("✓ Configuration validated successfully!")
    
    print(f"\nStarting Cal Men's Club Soccer Dashboard...")
    print(f"Environment: {app_config.ENVIRONMENT}")
    print(f"Debug Mode: {app_config.DEBUG}")
    print(f"Access URL: {app_config.BASE_URL}")
    print("\nTest Login Credentials:")
    print("  Executive: executive / executive123") 
    print("  Member: member / member123")
    
    # Run the app
    app.run(
        debug=app_config.DEBUG,
        host=app_config.HOST,
        port=app_config.PORT
    )