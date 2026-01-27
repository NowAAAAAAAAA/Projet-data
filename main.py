import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json
import os
import numpy as np

# Import layout
from src.components.layout import create_layout

# --- CONFIGURATION & DONNÉES ---
pd.options.mode.chained_assignment = None

print("Chargement des données...")
# Chemins relatifs (adaptés à l'arborescence utilisateur)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DETAIL_CSV = os.path.join(DATA_DIR, "cleaned", "data_detail.csv")
GEO_JSON = os.path.join(DATA_DIR, "raw", "etalab_communes.geojson")

# Lecture des données principales
df = pd.read_csv(DETAIL_CSV, dtype={'code_commune': str, 'code_departement': str, 'mois': str})

# Conversion de la date pour le tri correct
df['date_mutation'] = pd.to_datetime(df['date_mutation'])
df['month_date'] = df['date_mutation'].dt.to_period('M').astype(str) # Assurez format YYYY-MM

# --- PRÉPARATION DES FILTRES ---
# Liste des départements triée
departements = sorted(df['code_departement'].unique())

# Liste des types de biens
types_biens = sorted(df['type_local'].unique())

# Plage de dates (Mois min et max)
mes_mois = sorted(df['month_date'].unique())
min_date = mes_mois[0]
max_date = mes_mois[-1]

# Prix min/max
min_price = int(df['prix_m2'].min())
max_price = int(df['prix_m2'].max())

# Dates pour le DatePicker
min_date_dt = pd.to_datetime(min_date)
max_date_dt = pd.to_datetime(max_date)

# --- LOGIQUE GEOJSON (COPIÉE ET ADAPTÉE) ---
# Mapping des arrondissements pour le GeoJSON (Paris, Lyon, Marseille)
arrondissements_mapping = {
    ('Paris', 1): '75101', ('Paris', 2): '75102', ('Paris', 3): '75103', ('Paris', 4): '75104',
    ('Paris', 5): '75105', ('Paris', 6): '75106', ('Paris', 7): '75107', ('Paris', 8): '75108',
    ('Paris', 9): '75109', ('Paris', 10): '75110', ('Paris', 11): '75111', ('Paris', 12): '75112',
    ('Paris', 13): '75113', ('Paris', 14): '75114', ('Paris', 15): '75115', ('Paris', 16): '75116',
    ('Paris', 17): '75117', ('Paris', 18): '75118', ('Paris', 19): '75119', ('Paris', 20): '75120',
    ('Lyon', 1): '69381', ('Lyon', 2): '69382', ('Lyon', 3): '69383', ('Lyon', 4): '69384',
    ('Lyon', 5): '69385', ('Lyon', 6): '69386', ('Lyon', 7): '69387', ('Lyon', 8): '69388', ('Lyon', 9): '69389',
    ('Marseille', 1): '13201', ('Marseille', 2): '13202', ('Marseille', 3): '13203', ('Marseille', 4): '13204',
    ('Marseille', 5): '13205', ('Marseille', 6): '13206', ('Marseille', 7): '13207', ('Marseille', 8): '13208',
    ('Marseille', 9): '13209', ('Marseille', 10): '13210', ('Marseille', 11): '13211', ('Marseille', 12): '13212',
    ('Marseille', 13): '13213', ('Marseille', 14): '13214', ('Marseille', 15): '13215', ('Marseille', 16): '13216',
}

def extract_arrondissement_number(nom_commune):
    if 'Arrondissement' in nom_commune:
        parts = nom_commune.split()
        for i, part in enumerate(parts):
            if 'Arrondissement' in part and i > 0:
                try:
                    num_str = parts[i-1].replace('er', '').replace('e', '').replace('ème', '')
                    return int(num_str)
                except:
                    return None
    return None

def get_geojson_code(row):
    return row 

# Chargement GeoJSON
with open(GEO_JSON, 'r', encoding='utf-8') as f:
    geojson = json.load(f)

# --- PRÉ-CALCUL CENTROIDES DÉPARTEMENTS ---
dept_centers = {} 
temp_dept_coords = {} 

for feature in geojson['features']:
    try:
        code_com = feature['properties']['code']
        if code_com.startswith('97'):
            dept = code_com[:3]
        else:
            dept = code_com[:2]
            
        geom = feature['geometry']
        coords = []
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0] 
        elif geom['type'] == 'MultiPolygon':
            coords = geom['coordinates'][0][0] 
            
        if coords:
            lons = [p[0] for p in coords]
            lats = [p[1] for p in coords]
            avg_lon = sum(lons) / len(lons)
            avg_lat = sum(lats) / len(lats)
            
            if dept not in temp_dept_coords:
                temp_dept_coords[dept] = {'lats': [], 'lons': []}
            
            temp_dept_coords[dept]['lats'].append(avg_lat)
            temp_dept_coords[dept]['lons'].append(avg_lon)
            
    except Exception as e:
        continue

for dept, data in temp_dept_coords.items():
    if data['lats']:
        dept_centers[dept] = {
            'lat': sum(data['lats']) / len(data['lats']),
            'lon': sum(data['lons']) / len(data['lons'])
        }

print(f"Centraux calculés pour {len(dept_centers)} départements.")

# --- APPLICATION ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = "ImmoViz France"

# --- LAYOUT ---
app.layout = create_layout(departements, types_biens, min_price, max_price)

# --- CALLBACKS ---

def apply_geojson_logic(df_mapp):
    df_mapp['code_geojson'] = df_mapp['code_commune']
    return df_mapp

@app.callback(
    [Output('start-day', 'options'), Output('start-day', 'value')],
    [Input('start-month', 'value')],
    [State('start-day', 'value')]
)
def update_start_day(month, current_day):
    days_30 = [4, 6, 9, 11]
    if month == 2:
        max_days = 28
    elif month in days_30:
        max_days = 30
    else:
        max_days = 31
        
    options = [{'label': i, 'value': i} for i in range(1, max_days + 1)]
    
    new_day = current_day
    if current_day > max_days:
        new_day = max_days
        
    return options, new_day

@app.callback(
    [Output('end-day', 'options'), Output('end-day', 'value')],
    [Input('end-month', 'value')],
    [State('end-day', 'value')]
)
def update_end_day(month, current_day):
    days_30 = [4, 6, 9, 11]
    if month == 2:
        max_days = 28
    elif month in days_30:
        max_days = 30
    else:
        max_days = 31
        
    options = [{'label': i, 'value': i} for i in range(1, max_days + 1)]
    
    new_day = current_day
    if current_day > max_days:
        new_day = max_days
        
    return options, new_day


@app.callback(
    [Output('map-graph', 'figure'),
     Output('line-evol', 'figure'),
     Output('pie-type', 'figure'),
     Output('bar-top10', 'figure'),
     Output('hist-dist', 'figure'),
     Output('kpi-price', 'children'),
     Output('kpi-volume', 'children'),
     Output('kpi-top-city', 'children'),
     Output('kpi-top-price', 'children'),
     Output('kpi-surface', 'children')],
    [Input('btn-update', 'n_clicks')],
    [State('filter-dept', 'value'),
     State('filter-type', 'value'),
     State('start-day', 'value'),
     State('start-month', 'value'),
     State('end-day', 'value'),
     State('end-month', 'value'),
     State('filter-price', 'value'),
     State('filter-min-sales', 'value')]
)
def update_dashboard(n_clicks, selected_dept, selected_types, s_day, s_month, e_day, e_month, price_range, min_sales):
    try:
        start_date = pd.to_datetime(f"2023-{s_month}-{s_day}", format='%Y-%m-%d', errors='coerce')
        end_date = pd.to_datetime(f"2023-{e_month}-{e_day}", format='%Y-%m-%d', errors='coerce')
        
        if pd.isna(start_date):
            start_date = pd.to_datetime("2023-01-01")
        if pd.isna(end_date):
            end_date = pd.to_datetime("2023-12-31")
            
    except:
        start_date = pd.to_datetime("2023-01-01")
        end_date = pd.to_datetime("2023-12-31")
    
    mask = (df['date_mutation'] >= start_date) & (df['date_mutation'] <= end_date) & \
           (df['type_local'].isin(selected_types)) & \
           (df['prix_m2'] >= price_range[0]) & (df['prix_m2'] <= price_range[1])
    
    if selected_dept != 'all':
        mask = mask & (df['code_departement'] == selected_dept)
    
    filtered_df = df[mask]
    
    if filtered_df.empty:
        empty_fig = px.scatter(title="Aucune donnée disponible pour ces filtres")
        return empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, "-", "0", "-", "-", "-"

    # --- KPIs ---
    avg_price = filtered_df['prix_m2'].mean()
    total_vol = len(filtered_df)
    avg_surface = filtered_df['surface_reelle_bati'].mean()
    
    city_stats = filtered_df.groupby('nom_commune').agg({'prix_m2': 'mean', 'valeur_fonciere': 'count'})
    valid_cities = city_stats[city_stats['valeur_fonciere'] >= 5]
    if not valid_cities.empty:
        top_city_row = valid_cities['prix_m2'].idxmax()
        top_city_price = valid_cities['prix_m2'].max()
    else:
        top_city_row = "-"
        top_city_price = 0

    kpi_price_str = f"{avg_price:.0f}"
    kpi_vol_str = f"{total_vol:,}".replace(",", " ")
    kpi_top_city_str = str(top_city_row)
    kpi_top_price_str = f"{top_city_price:.0f} €/m²"
    kpi_surf_str = f"{avg_surface:.0f}"

    # --- MAP DATA PREPARATION ---
    df_map_ag = filtered_df.groupby(['code_commune', 'nom_commune', 'code_departement'])['prix_m2'].agg(['mean', 'count']).reset_index()
    df_map_ag.columns = ['code_commune', 'nom_commune', 'code_departement', 'prix_moyen', 'nb_ventes']
    
    min_s = min_sales if min_sales is not None else 0
    df_map_ag = df_map_ag[df_map_ag['nb_ventes'] >= min_s] 
    
    if not df_map_ag.empty:
        df_map_ag = apply_geojson_logic(df_map_ag)
        
        map_center = {"lat": 46.5, "lon": 2.5} 
        zoom = 5

        if selected_dept != 'all':
             if selected_dept in dept_centers:
                 map_center = dept_centers[selected_dept]
                 if len(selected_dept) == 3: # DOM
                     zoom = 8.5
                 elif selected_dept == '75': # Paris
                     zoom = 11
                 else:
                     zoom = 8.5 
             else:
                 zoom = 6 
        else:
             zoom = 5
        
        fig_map = px.choropleth_mapbox(
            df_map_ag,
            geojson=geojson,
            locations='code_geojson',
            featureidkey="properties.code",
            color='prix_moyen',
            color_continuous_scale="Spectral_r",
            range_color=[1000, 8000],
            mapbox_style="carto-positron",
            zoom=zoom, 
            center=map_center,
            opacity=0.6,
            hover_name='nom_commune',
            hover_data={'prix_moyen':':.0f', 'nb_ventes':True},
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    else:
        fig_map = px.scatter_mapbox(bs="carto-positron", zoom=5)

    # --- CHARTS ---
    
    # 1. Line
    df_evol = filtered_df.groupby('month_date')['prix_m2'].mean().reset_index()
    df_evol['month_date'] = df_evol['month_date'].astype(str)
    fig_line = px.line(df_evol, x='month_date', y='prix_m2', markers=True)
    fig_line.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 2. Pie
    fig_pie = px.pie(filtered_df, names='type_local', values='valeur_fonciere', hole=0.4,
                     color='type_local', color_discrete_map={'Maison':'#e74c3c', 'Appartement':'#3498db'})
    fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
    
    # 3. Bar Top 10
    top_cities = city_stats[city_stats['valeur_fonciere'] > 10].nlargest(10, 'prix_m2').sort_values('prix_m2', ascending=True).reset_index()
    if not top_cities.empty:
        fig_bar = px.bar(top_cities, x='prix_m2', y='nom_commune', orientation='h', 
                         text_auto='.0f', color='prix_m2', color_continuous_scale='Viridis')
        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
    else:
        fig_bar = px.bar(title="Pas assez de données")

    # 4. Hist
    fig_hist = px.histogram(filtered_df, x="prix_m2", nbins=50)
    fig_hist.update_layout(bargap=0.1, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    return fig_map, fig_line, fig_pie, fig_bar, fig_hist, kpi_price_str, kpi_vol_str, kpi_top_city_str, kpi_top_price_str, kpi_surf_str

if __name__ == '__main__':
    app.run(debug=True)
