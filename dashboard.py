# dashboard.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json
import os

# --- CHARGEMENT DES DONNÉES CSV ---
print("Chargement des données CSV (cela peut prendre quelques secondes)...")
MAP_CSV = os.path.join("data", "cleaned", "data_map.csv")
DETAIL_CSV = os.path.join("data", "cleaned", "data_detail.csv")
GEO_JSON = os.path.join("data", "raw", "communes.geojson")

# Lecture avec types optimisés pour gagner de la RAM
df_map = pd.read_csv(MAP_CSV, dtype={'code_commune': str, 'code_departement': str})
df_detail = pd.read_csv(DETAIL_CSV, dtype={'code_commune': str, 'code_departement': str})

# Chargement GeoJSON
with open(GEO_JSON, 'r') as f:
    geojson = json.load(f)

print("Données chargées.")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX]) # Thème 'LUX' plus pro

# --- LAYOUT ---
app.layout = dbc.Container([
    # Titre
    dbc.Row([
        dbc.Col(html.H1("Observatoire National de l'Immobilier 2023", className="text-center my-4 text-primary"), width=12)
    ]),

    # KPIs (Chiffres clés)
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Prix Moyen France", className="card-title"),
                html.H2(f"{df_detail['prix_m2'].mean():.0f} €/m²", className="text-success")
            ])
        ], color="light", outline=True), width=4),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Volume de Ventes", className="card-title"),
                html.H2(f"{len(df_detail):,}".replace(',', ' '), className="text-info")
            ])
        ], color="light", outline=True), width=4),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Commune la + chère", className="card-title"),
                html.H2(df_map.sort_values('prix_moyen', ascending=False).iloc[0]['nom_commune'], className="text-warning")
            ])
        ], color="light", outline=True), width=4),
    ], className="mb-4"),

    # Onglets
    dcc.Tabs([
        # ONGLET 1 : CARTOGRAPHIE
        dcc.Tab(label='Cartographie Interactive', children=[
            dbc.Row([
                dbc.Col([
                    html.P("L'affichage de toute la France peut être lent. Zoomez pour explorer.", className="text-muted mt-2"),
                    dcc.Graph(id='map-graph', style={'height': '80vh'})
                ])
            ])
        ]),

        # ONGLET 2 : STATISTIQUES AVANCÉES
        dcc.Tab(label='Analyses & Statistiques', children=[
            # Ligne 1 : Évolution et Répartition
            dbc.Row([
                dbc.Col([
                    dbc.Card([dbc.CardHeader("Évolution des prix au cours de l'année"), 
                              dbc.CardBody(dcc.Graph(id='line-evol'))])
                ], width=8),
                dbc.Col([
                    dbc.Card([dbc.CardHeader("Maison vs Appartement"), 
                              dbc.CardBody(dcc.Graph(id='pie-type'))])
                ], width=4),
            ], className="mt-4"),

            # Ligne 2 : Top 10 et Distribution
            dbc.Row([
                dbc.Col([
                    dbc.Card([dbc.CardHeader("Top 10 Villes les plus chères (>50 ventes)"), 
                              dbc.CardBody(dcc.Graph(id='bar-top10'))])
                ], width=6),
                dbc.Col([
                    dbc.Card([dbc.CardHeader("Distribution des prix au m²"), 
                              dbc.CardBody(dcc.Graph(id='hist-dist'))])
                ], width=6),
            ], className="mt-4")
        ]),
    ])
], fluid=True)

# --- CALLBACKS ---
@app.callback(
    Output('map-graph', 'figure'),
    Input('map-graph', 'id')
)
def update_map(_):
    # Pour la France entière, on limite la résolution pour ne pas faire planter le navigateur
    # On affiche tout, mais Dash gère mieux les gros volumes via mapbox
    fig = px.choropleth_mapbox(
        df_map,
        geojson=geojson,
        locations='code_commune',
        featureidkey="properties.code",
        color='prix_moyen',
        color_continuous_scale="Spectral_r",
        range_color=[1000, 8000], # On sature à 8000 pour bien voir les nuances en province
        mapbox_style="carto-positron",
        zoom=5, center = {"lat": 46.5, "lon": 2.5},
        opacity=0.5,
        hover_name='nom_commune',
        hover_data={'prix_moyen':':.0f', 'nb_ventes':True}
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

@app.callback(
    [Output('line-evol', 'figure'),
     Output('pie-type', 'figure'),
     Output('bar-top10', 'figure'),
     Output('hist-dist', 'figure')],
    Input('map-graph', 'id')
)
def update_stats(_):
    # 1. Line Chart : Evolution mensuelle
    df_evol = df_detail.groupby('mois')['prix_m2'].mean().reset_index()
    # Conversion 'mois' en string pour l'affichage correct
    df_evol['mois'] = df_evol['mois'].astype(str)
    fig_line = px.line(df_evol, x='mois', y='prix_m2', markers=True, title="Prix moyen mensuel")
    
    # 2. Sunburst / Pie : Répartition
    fig_pie = px.sunburst(df_detail, path=['type_local', 'nature_mutation'], values='valeur_fonciere',
                          color='type_local', color_discrete_map={'Maison':'#EF553B', 'Appartement':'#636EFA'})
    
    # 3. Bar Chart : Top 10 Chères (Filtre sur volume > 50 pour éviter les micro-villages)
    top_cities = df_map[df_map['nb_ventes'] > 50].nlargest(10, 'prix_moyen').sort_values('prix_moyen')
    fig_bar = px.bar(top_cities, x='prix_moyen', y='nom_commune', orientation='h', 
                     text_auto='.0f', color='prix_moyen', color_continuous_scale='Viridis')
    
    # 4. Histogramme : Distribution
    fig_hist = px.histogram(df_detail, x="prix_m2", nbins=50, title="Répartition des prix (Gaussienne)")
    fig_hist.update_layout(bargap=0.1)

    return fig_line, fig_pie, fig_bar, fig_hist

if __name__ == '__main__':
    app.run(debug=True)