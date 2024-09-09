import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Cargar el archivo CSV
df = pd.read_csv('datos_Con_date_Seasons.csv')

variable_respuesta = "Rented Bike Count"
available_indicators = [col for col in df.columns if col not in [variable_respuesta, 'Date', "Seasons","Winter","Summer","Spring","Autumn","Dew point temperature(C)",
                                                                 "Solar Radiation (MJ/m2)"]]

df["Holiday"]=df["Holiday"].map({0:"No Holiday",1:"Holiday"})
df["Functioning Day"]=df["Functioning Day"].map({0:"Yes",1:"No"})

# Filtrar las columnas numéricas y categóricas
numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

# Convertir la columna Date en formato datetime
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

# Crear columnas para el mes y el año
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

# Crear una columna que combine año y mes
df['YearMonth'] = df['Date'].dt.to_period('M')

# Obtener las estaciones (ya presentes en la columna 'Seasons')
season_labels = {i: season for i, season in enumerate(df['Seasons'].unique())}

# Obtener los valores únicos de YearMonth para el slider
unique_year_month = df['YearMonth'].unique()

# Crear marcas para el slider de meses
marks_month = {i: str(ym) for i, ym in enumerate(unique_year_month)}

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='Hour'
            )
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': variable_respuesta, 'value': variable_respuesta}],
                value=variable_respuesta
            )
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    html.Div([
        dcc.Dropdown(
            id='chart-type',
            value='scatter',  # Valor por defecto
        )
    ], style={'width': '48%', 'display': 'inline-block'}),

    dcc.Graph(id='indicator-graphic'),

    # RadioItems para seleccionar entre agrupar por mes o por estación
    html.Div([
        dcc.RadioItems(
            id='grouping-choice',
            options=[
                {'label': 'Group by Month', 'value': 'month'},
                {'label': 'Group by Season', 'value': 'season'}
            ],
            value='month',
            labelStyle={'display': 'inline-block'}
        )
    ]),

    # Slider de meses
    html.Div(id='month-slider-container', children=[
        html.Label('Select Month:'),
        dcc.Slider(
            id='month--slider',
            min=0,
            max=len(unique_year_month) - 1,
            value=len(unique_year_month) - 1,
            marks=marks_month,
            step=None
        )
    ], style={'width': '48%', 'display': 'inline-block'}),

    # Slider de estaciones
    html.Div(id='season-slider-container', children=[
        html.Label('Select Season:'),
        dcc.Slider(
            id='season--slider',
            min=0,
            max=len(season_labels) - 1,
            value=0,
            marks=season_labels,
            step=None
        )
    ], style={'width': '48%', 'display': 'none'})  # Se oculta al inicio
])

# Opciones de gráficos para variables numéricas
numeric_graphs = [
    {'label': 'Scatter Plot', 'value': 'scatter'},
    {'label': 'Heatmap', 'value': 'heatmap'},
    {'label': 'Bar Plot', 'value': 'bar'},
    {'label': 'Box Plot', 'value': 'box'},
    {'label': 'Histogram', 'value': 'histogram'}  # Agregar histograma
]

# Opciones de gráficos para variables categóricas
categorical_graphs = [
    {'label': 'Bar Plot', 'value': 'bar'},
    {'label': 'Pie Chart', 'value': 'pie'}
]

# Callback para actualizar las opciones del gráfico según la variable seleccionada
@app.callback(
    [Output('chart-type', 'options'),
     Output('chart-type', 'value')],
    [Input('xaxis-column', 'value')]
)
def update_chart_type_options(selected_var):
    if selected_var in numeric_columns:
        return numeric_graphs, 'scatter'  # Mostrar gráficos para variables numéricas y establecer scatter como predeterminado
    else:
        return categorical_graphs, 'bar'  # Mostrar gráficos para variables categóricas y establecer bar como predeterminado

# Callback para mostrar u ocultar el slider adecuado
@app.callback(
    [Output('month-slider-container', 'style'),
     Output('season-slider-container', 'style')],
    [Input('grouping-choice', 'value')]
)
def toggle_sliders(grouping_choice):
    if grouping_choice == 'month':
        return {'width': '48%', 'display': 'inline-block'}, {'display': 'none'}
    elif grouping_choice == 'season':
        return {'display': 'none'}, {'width': '48%', 'display': 'inline-block'}

# Callback para actualizar el gráfico dependiendo del slider seleccionado
@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('yaxis-column', 'value'),
     Input('grouping-choice', 'value'),
     Input('month--slider', 'value'),
     Input('season--slider', 'value'),
     Input('chart-type', 'value')])
def update_graph(xaxis_column_name, yaxis_column_name,
                 grouping_choice,
                 month_value, season_value, chart_type):
    
    if grouping_choice == 'month':
        selected_month = unique_year_month[month_value]
        selected_year = selected_month.year
        selected_month_only = selected_month.month
        # Filtrar los datos de df para el mes y año seleccionados
        dff = df[(df['Year'] == selected_year) & (df['Month'] == selected_month_only)]
    elif grouping_choice == 'season':
        selected_season = list(season_labels.values())[season_value]
        # Filtrar los datos de df para la temporada seleccionada
        dff = df[df['Seasons'] == selected_season]

    # Crear el gráfico en función del tipo seleccionado
    if chart_type == 'scatter':
        fig = px.scatter(dff, x=xaxis_column_name, y=yaxis_column_name,
                         labels={xaxis_column_name: xaxis_column_name, yaxis_column_name: yaxis_column_name},
                         trendline='ols')  # Agregar la línea de tendencia (regresión lineal)
    elif chart_type == 'heatmap':
        fig = px.density_heatmap(dff, x=xaxis_column_name, y=yaxis_column_name)
    elif chart_type == 'bar':
        fig = px.bar(dff, x=xaxis_column_name, y=yaxis_column_name)
    elif chart_type == 'pie':
        fig = px.pie(dff, names=xaxis_column_name, values=yaxis_column_name)
    elif chart_type == 'box':
        fig = px.box(dff, x=xaxis_column_name, y=yaxis_column_name)
    elif chart_type == 'histogram':  # Agregar histograma
        fig = px.histogram(dff, x=xaxis_column_name, nbins=20, labels={xaxis_column_name: xaxis_column_name})

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')
    fig.update_xaxes(title=xaxis_column_name, type='category' if xaxis_column_name in categorical_columns else 'linear') 
    fig.update_yaxes(title=yaxis_column_name, type='linear') 

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
