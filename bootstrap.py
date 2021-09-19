import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import os
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
from dotenv import load_dotenv, find_dotenv

# import plotly.offline as py
# import plotly.graph_objects as go

# API Token for MapBox
load_dotenv(find_dotenv())
mapbox_access_token = os.environ['MAPBOX_ACCESS_TOKEN']

# Set Pandas Options for infinite equal to nan to resolve schools without enrollment numbers
pd.set_option('use_inf_as_na', True)

# Load existing Data
df = pd.read_csv('logged_data.csv')
df_lat_lon = pd.read_csv('school_lat_lon.csv')

# Store known static numbers from official dashboard
# Existing Enrollment Data 
enrollment = 21568

# Last effective log date
last_log_date = str(df.date.max())

# Merge Dataframes and Calculated Required Insights
df_per_cases = pd.merge(df, df_lat_lon, on='school')

# Calculate Current Active Case Percentages
df_per_cases['% Active Cases'] = (df_per_cases['active_cases'] / df_per_cases['Enrollment'] * 100).round(2)

# Isolate Staff and Student Data
df_students = df[df['students_staff'] == 'students']
df_staff = df[df['students_staff'] == 'staff']

# Update with existing
students_current = df[(df.date == df.date.max()) & (df.students_staff == 'students')].reset_index(drop=True)
students_current = students_current[['school', 'school_type', 'active_cases']].sort_values('active_cases',
                                                                                           ascending=False)

# df_staff = df[(df.date == df.date.max()) & (df.students_staff == 'staff')].reset_index(drop=True)
# df_staff = df_staff.sort_values('active_cases', ascending=False)
# print(df_staff)

df3 = pd.merge(students_current, df_lat_lon, on='school')

df_overview = df3[['school', 'Enrollment', 'active_cases']]
df_overview['% Active Cases'] = (df_overview['active_cases'] / df_overview['Enrollment'] * 100).round(2)
df_overview.columns = ['School', 'Enrollment', 'Active Cases', '% Active Cases']
df_overview = df_overview.sort_values('% Active Cases', ascending=False, na_position='last')

df3 = df3[['school', 'latitude', 'longitude', 'active_cases']]

df_trend = df_students.copy()
df_trend.date = pd.to_datetime(df_trend.date)

# Card Calculations 

students_case_count = students_current['active_cases'].sum()
staff_case_count = df_staff['active_cases'].sum()
per_active_cases = ((students_case_count / enrollment) * 100).round(2)

# Figures and Charts

fig_staff = px.bar(df_staff, x="school", y="active_cases", color="school", text='active_cases', height=800)
fig_staff.update_xaxes(title_text='Schools')
fig_staff.update_yaxes(title_text=f'Active Cases for Staff as of {last_log_date}')

fig_staff.update_layout(
    xaxis=dict(
        showline=True,
        showgrid=False,
        showticklabels=True,
        linecolor='rgb(204, 204, 204)',
        linewidth=2,
        ticks='outside',
        tickfont=dict(
            family='Arial',
            size=12,
            color='rgb(82, 82, 82)',
        ),
    ),
    yaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
    ),
    autosize=False,
    margin=dict(
        autoexpand=False,
        l=100,
        r=20,
        t=110,
    ),
    showlegend=True,
    plot_bgcolor='white'
)

# App Styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

##################
df3['text'] = df3['school'] + df['active_cases'].astype(str)

df_sub = df3.copy()
df_sub['active_cases'] = df_sub['active_cases'].astype('int32')

px.set_mapbox_access_token(mapbox_access_token)

map_fig = px.scatter_mapbox(df_sub,
                            lat='latitude',
                            lon='longitude',
                            size='active_cases',
                            color='active_cases',
                            center=dict(lat=33.10942346797352, lon=-96.67715740805163),
                            mapbox_style='light',
                            hover_name='school',
                            color_continuous_scale=px.colors.sequential.Bluered,
                            zoom=12,
                            opacity=0.4,
                            height=800
                            )

map_fig.update_traces(
    text='school'
)

cards = dbc.CardGroup(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H3(f"{students_case_count} Active Student Cases", className="card-title"),
                    # html.P( "Click to view specific school trend", className="card-text", ), dbc.Button( "Click
                    # here",id='school_chart_button', color="primary", className="btn btn-primary disabled",
                    # n_clicks=0 ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H3(f"{per_active_cases}% of Current Enrollment", className="card-title"),
                    # html.P(
                    #     "Click to view per active case by school.",
                    #     className="card-text",
                    # ),
                    # dbc.Button(
                    #     "Click here", color="primary", className="btn btn-primary disabled"
                    # ),
                ]
            )
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H3(f"{staff_case_count} Active Staff Cases", className="card-title"),
                    # html.P(
                    #     "Click to view staff by school",
                    #     className="card-text",
                    # ),
                    # dbc.Button(
                    #     "Click here", color="primary", className="btn btn-primary disabled"
                    # ),
                ]
            )
        ),
    ]
)

# styling the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# padding for the page content
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}


@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        return [
            html.H1(f'Allen ISD COVID-19 Dashboard',
                    style={'textAlign': 'left'}),
            html.H5(f'Last updated: {last_log_date}'),
            html.Hr(),
            cards, html.Hr(),
            dcc.Graph(
                id='map',
                figure=map_fig
            ),

        ]
    elif pathname == "/page-1":
        return [html.H1('School Active Case Summary Table',
                        style={'textAlign': 'left'}),
                dcc.Dropdown(id='school_choice',
                             options=[{'label': x, 'value': x}
                                      for x in sorted(df_students.school.unique())],
                             value='VAUGHAN'
                             ),
                html.Hr(),
                dcc.Graph(
                    id='students_graph',
                    figure={}
                )]
    elif pathname == "/page-2":
        return [
            html.Div([
                html.H1(children='Student Cases Trends'),
                html.Hr(),
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in df_overview.columns],
                    data=df_overview.to_dict('records')),
            ])]
    elif pathname == "/page-3":
        return [
            html.Div([
                html.H1(children='Allen ISD Student Case Count Map'),
                html.Hr(),

                dcc.Graph(
                    id='map',
                    figure=map_fig
                )]),
        ]
    elif pathname == "/page-4":
        return [
            html.Div([
                html.H1(children='Current Allen ISD Staff Active Case Count by School'),
                html.Hr(),

                dcc.Graph(
                    id='staff',
                    figure=fig_staff
                ),
            ])]
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


@app.callback(
    Output(component_id='students_graph', component_property='figure'),
    Input(component_id='school_choice', component_property='value')
)
def interactive_graph(school_choice):
    df_students_choice = df_students[df_students.school == school_choice]
    fig_students_choice = px.line(df_students_choice, x="date", y="active_cases", text='active_cases', height=800)
    fig_students_choice.update_traces(textposition='bottom right')
    fig_students_choice.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=False,
        ),
        autosize=False,
        margin=dict(
            autoexpand=False,
            l=100,
            r=20,
            t=110,
        ),
        showlegend=False,
        plot_bgcolor='white'
    )
    return fig_students_choice


# Alert notification

alert = html.Div(
    [
        dbc.Button(
            "Disclaimer", id="alert-toggle-auto", className="mr-1", n_clicks=0
        ),
        html.Hr(),
        dbc.Alert(
            "This dashboard uses data from the Allen ISD daily covid case reporting to map and show trends within our "
            "local schools. Developed by a concerned parent and for concerned parents. If you have concerns about the "
            "information presented I recommend contacting your schools administrative staff. Stay safe.",
            id="alert-auto",
            is_open=True,
            duration=4000,
        ),
    ]
)


@app.callback(
    Output("alert-auto", "is_open"),
    [Input("alert-toggle-auto", "n_clicks")],
    [State("alert-auto", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open


sidebar = html.Div(
    [
        html.P(
            "Navigation", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("School Trend", href="/page-1", active="exact"),
                dbc.NavLink("Percent Active Cases", href="/page-2", active="exact"),
                dbc.NavLink("School Map", href="/page-3", active="exact"),
                dbc.NavLink("Staff", href="/page-4", active="exact"),
                dbc.NavLink("Official Dashboard",
                            href="https://docs.google.com/spreadsheets/d/e/2PACX-1vS7pP0EYu0ZhN-VJLX6b_OqFqXwFv_3ndAtb41T12APwCnNqcOJ3mEPs_wFcA36jeXABZ0xi2yofmJ6/pubhtml?gid=0&single=true",
                            active="exact"),
                html.Hr(),
            ],
            vertical=True,
            pills=True,
        ), alert
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    content
])


@app.callback(
    Output("example-output", "children"), [Input("school_chart_button", "n_clicks")]
)
def on_button_click(n):
    if n is None:
        return "Not clicked."
    else:
        return print(f"Clicked {n} times.")


if __name__ == '__main__':
    app.run_server(debug=False, port=3000, dev_tools_ui=False)

# Allen Center Lat Lon 33.10942346797352, -96.67715740805163
