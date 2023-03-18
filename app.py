from dash import html, dcc, Input, Output
import altair as alt
import dash
import pandas as pd
from dash import dash_table as dt
from vega_datasets import data
from dash_bootstrap_templates import load_figure_template

load_figure_template("LUX")

tabs_styles = {
    'height': '44px',
    "margin-left": "30rem",
    "margin-right": "50rem"
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "25rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "30rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    'marginBottom': 50, 
    'marginTop': 25
}

def explode_rows(df, value, column, replacement):
    ind = df.loc[df[column] == value].index[0]
    df.at[ind, column] = replacement
    df = df.explode(column)


def get_clean_data():
    dino_data = pd.read_csv("data/data.csv")
    split_str = dino_data["period"].str.split(" ")
    dino_data["period_wo_year"] = [" ".join(x[:2]) for x in split_str]

    omni_herb = ["herbivorous", "omnivorous"]
    explode_rows(dino_data, "herbivorous/omnivorous", "diet", omni_herb)   
    dino_data["diet"] = dino_data["diet"].str.capitalize()
    dino_data["name"] = dino_data["name"].str.capitalize()
    dino_data["type"] = dino_data["type"].str.capitalize()

    north_africa_countries = ["Algeria", "Morocco", "Tunisia", "Egypt", 
                "Libya", "Sudan", "Western Sahara",
                "Mauritania", "South Sudan", "Chad"]
    explode_rows(dino_data, "North Africa", "lived_in", north_africa_countries)
    # Not sure why need to do it again
    dino_data = dino_data.explode("lived_in")

    dino_data = dino_data.replace("USA", "United States")
    dino_data = dino_data.replace("Wales", "United Kingdom")
    dino_data = dino_data.replace("USA", "United States")
    dino_data["diet"].fillna("Unknown", inplace = True)

    return dino_data

# Read in global data
dino_data = get_clean_data()
iso = pd.read_csv("data/iso.csv")

variable_list = ['population', 'engineers', 'hurricanes']

# Setup app and layout/frontend
app = dash.Dash(__name__,  external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

sidebar_tab1 = html.Div(
    [
        html.Label([
        'Select a period:',
        dcc.Dropdown(
            id='period-widget',
            value='Any',  
            options=["Any"] + sorted(dino_data["period_wo_year"].unique().tolist()))]),
        html.Br(),
        html.Label([
        "Select the country that the dinosaur lived in:",
        dcc.Dropdown(
            id='loc-widget',
            value='All',  
        )
     ]),
    ],
    style=SIDEBAR_STYLE
)

sidebar_tab2 = html.Div(
    [
        html.Label([
        'Select category:',
        dcc.RadioItems(
            id = "diet",
            options = ["All"] + dino_data["diet"].unique().tolist(), 
            value = 'All')
     ]),
    ],
    style=SIDEBAR_STYLE
)

period_tab = html.Div(
    children = [
        html.H5("What types of dinosaurs can be found in different periods and countries?"),
        html.Iframe(
            id='hist',
            style={"border-width": '0', 'width': '100%', "height": "230px"}
        ),
        html.Br(),
        html.H5("What are some random dinosaurs of these types?"),
        dt.DataTable(
            id = 'rand_dino_table'
        ),
        sidebar_tab1], 
        style=CONTENT_STYLE
)

map_tab = html.Div(
    children = [
        html.H4("What species of dinosaurs are found around the world?"),
        html.Iframe(
            id='map',
            style={"border-width": '0', "width": "100%", "height": "400px"}
        ),
        sidebar_tab2],
        style = CONTENT_STYLE
)

app.layout = html.Div([
    dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
        dcc.Tab(label='Tab One', value='tab-1-example-graph', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Tab Two', value='tab-2-example-graph', style=tab_style, selected_style=tab_selected_style),
    ], style = tabs_styles),
    html.Div(id='tabs-content-example-graph', children = [period_tab, map_tab])
])

@app.callback(
    Output('loc-widget', 'options'),
    Input('period-widget', 'value'))
def set_loc_options(period_widget):
    results_df = dino_data
    if period_widget != "Any":
        results_df = dino_data.query("period_wo_year == @period_widget")
    return ["All"] + sorted(results_df["lived_in"].astype(str).unique().tolist())

@app.callback(Output('tabs-content-example-graph', 'children'),
              [Input('tabs-example-graph', 'value')])
def render_content(tab):
    if tab == 'tab-1-example-graph':
        return period_tab
    elif tab == 'tab-2-example-graph':
        return map_tab

# Set up callbacks/backend
@app.callback(
        Output('hist', 'srcDoc'),
        [Input('period-widget', 'value'),
         Input('loc-widget', 'value')]
)
def plot_altair(period_widget, loc_widget):
    result_df = dino_data
    title = f"Types of Dinosaurs"
    if (period_widget != "Any"):
        result_df = result_df.query("period_wo_year == @period_widget")
        title = title + f" that lived during {str(period_widget)}"
    if (loc_widget != "All"):
        result_df = result_df.query("lived_in == @loc_widget")
        title = title + f" and in {str(loc_widget)}"
    chart = alt.Chart(result_df).mark_bar().encode(
        x = "count()",
        y = alt.Y("type", sort = "y", title = "Dino Type"),
    ).configure_mark(
        color='#4b572f'
    ).configure_axis(
        grid=False
    ).properties(
        title=title
    )
    return chart.to_html()

@app.callback(
        Output('rand_dino_table', 'data'),
        [Input('period-widget', 'value'),
         Input('loc-widget', 'value')]
)
def find_random_dinos(period_widget, loc_widget):
    result_df = dino_data
    if (period_widget != "Any"):
        result_df = result_df.query("period_wo_year == @period_widget")
    if (loc_widget != "All"):
        result_df = result_df.query("lived_in == @loc_widget")
    type_list = result_df["type"].unique()
    if len(type_list) == 0:
        df = pd.DataFrame()
        return df.to_dict('records')
    df_list = []
    for type in type_list:
        df_list.append(result_df.query("type == @type").sample())
    final_df = pd.concat(df_list)[["name", "type", "link"]].sort_values(by=['type'])
    return final_df.to_dict('records')


@app.callback(
        Output('map', 'srcDoc'),
        Input('diet', 'value')
)
def plot_altair_map(diet): 
    geo_dino = dino_data
    if diet != "All":
        geo_dino = dino_data.query("diet == @diet") 

    geo_dino = geo_dino.groupby("lived_in").count().reset_index()
    geo_dino = geo_dino.merge(iso[["English short name lower case", "Numeric code"]], 
                          how='outer', left_on='lived_in', right_on='English short name lower case')   

    source = alt.topo_feature(data.world_110m.url, "countries")

    background = alt.Chart(source).mark_geoshape(fill="white")

    foreground = (
        alt.Chart(source)
        .mark_geoshape(stroke="black", strokeWidth=0.15)
        .encode(
            color= alt.condition("datum.species == 'null'", alt.value('white'), 
                          alt.Color("species:N", scale=alt.Scale(scheme="lightgreyteal"), legend=None)),
            tooltip=[
                alt.Tooltip("English short name lower case:N", title="Country"),
                alt.Tooltip("species:Q", title="Number of Species"),
            ],
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(geo_dino, "Numeric code", ["species", "English short name lower case"]),
        )
    )

    final_map = (
        (background + foreground)
        .configure_view(strokeWidth=0)
        .properties(width=850, height=350, padding={"left": 0, "right": 0, "bottom": 0, "top": 0})
        .project("naturalEarth1")
    )
  
    return final_map.to_html()

if __name__ == '__main__':
    app.run_server(debug=True)
