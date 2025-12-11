# dashboard.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json
import os

# --- CHARGEMENT ---
DATA_PATH = os.path.join("data", "cleaned", "dvf_idf.parquet")
AGG_PATH = os.path.join("data", "cleaned", "stats_communes.parquet")
GEO_PATH = os.path.join("data", "raw", "communes.geojson")

print("⏳ Chargement des données...")
# 1. Données agrégées (Légères)
df_agg = pd.read_parquet(AGG_PATH)
# 2. Données détaillées (Lourdes, on pourrait ne charger que sur demande, mais ok pour IDF)
df_detail = pd.read_parquet(DATA_PATH)
# 3. Le GeoJSON
with open(GEO_PATH, 'r') as f:
    geojson = json.load(f)
print("✅ Tout est chargé.")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# --- LAYOUT ---
app.layout = dbc.Container([
    html.H1("DVF 2023 : Immobilier Île-de-France", className="my-4 text-center"),

    dcc.Tabs([
        # --- ONGLET 1 : LA CARTE ---
        dcc.Tab(label='Vue Régionale (Carte)', children=[
            dbc.Row([
                dbc.Col([
                    html.P("Survolez une commune pour voir son prix moyen.", className="mt-3"),
                    dcc.Graph(id='choropleth-map', style={'height': '75vh'})
                ], width=12)
            ])
        ]),

        # --- ONGLET 2 : COMPARATEUR ---
        dcc.Tab(label='Comparateur de Villes', children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Ville A"),
                    dcc.Dropdown(
                        id='city-a',
                        options=[{'label': n, 'value': c} for n, c in zip(df_agg['nom_commune'], df_agg['code_commune'])],
                        value='75056' # Code INSEE Paris (générique) ou un arrondissement
                    )
                ], width=6, className="mt-3"),
                dbc.Col([
                    html.Label("Ville B"),
                    dcc.Dropdown(
                        id='city-b',
                        options=[{'label': n, 'value': c} for n, c in zip(df_agg['nom_commune'], df_agg['code_commune'])],
                        value='77108' # Code INSEE Champs-sur-Marne
                    )
                ], width=6, className="mt-3")
            ]),
            
            html.Hr(),
            
            dbc.Row([
                dbc.Col(dcc.Graph(id='comp-bar-price'), width=6),
                dbc.Col(dcc.Graph(id='comp-box-dist'), width=6)
            ])
        ])
    ])
], fluid=True)

# --- CALLBACKS ---

@app.callback(
    Output('choropleth-map', 'figure'),
    Input('choropleth-map', 'id') # Dummy input juste pour initialiser
)
def update_map(_):
    # Carte Choroplèthe (Villes colorées)
    fig = px.choropleth_mapbox(
        df_agg,
        geojson=geojson,
        locations='code_commune',     # La colonne du DF qui contient le code INSEE
        featureidkey="properties.code", # La clé du GeoJSON qui contient le code INSEE
        color='prix_moyen',
        color_continuous_scale="RdYlGn_r", # Rouge = Cher, Vert = Pas cher (inversement _r)
        range_color=[2000, 12000],
        mapbox_style="carto-positron",
        zoom=8.5, center = {"lat": 48.85, "lon": 2.35},
        opacity=0.6,
        hover_name='nom_commune',
        hover_data={'prix_moyen':':.0f'}
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

@app.callback(
    [Output('comp-bar-price', 'figure'),
     Output('comp-box-dist', 'figure')],
    [Input('city-a', 'value'),
     Input('city-b', 'value')]
)
def update_comparison(city_a_code, city_b_code):
    # Filtrer les données détaillées pour les deux villes choisies
    dff = df_detail[df_detail['code_commune'].isin([city_a_code, city_b_code])]
    
    if dff.empty:
        return px.bar(), px.box()

    # 1. Bar Chart : Prix Moyen
    avg_data = dff.groupby('nom_commune')['prix_m2'].mean().reset_index()
    fig_bar = px.bar(avg_data, x='nom_commune', y='prix_m2', 
                     color='nom_commune', title="Comparaison Prix Moyen (m²)")
    
    # 2. Box Plot : Distribution des prix (Montre l'écart type, les min/max)
    fig_box = px.box(dff, x='nom_commune', y='prix_m2', 
                     color='nom_commune', title="Distribution des prix")
    
    return fig_bar, fig_box

if __name__ == '__main__':
    app.run(debug=True)