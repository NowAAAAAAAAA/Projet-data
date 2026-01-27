from dash import dcc, html
import dash_bootstrap_components as dbc

# Dictionnaire des noms de départements pour l'affichage
DEPARTEMENTS = {
    '01': 'Ain', '02': 'Aisne', '03': 'Allier', '04': 'Alpes-de-Haute-Provence', 
    '05': 'Hautes-Alpes', '06': 'Alpes-Maritimes', '07': 'Ardèche', '08': 'Ardennes', 
    '09': 'Ariège', '10': 'Aube', '11': 'Aude', '12': 'Aveyron', '13': 'Bouches-du-Rhône', 
    '14': 'Calvados', '15': 'Cantal', '16': 'Charente', '17': 'Charente-Maritime', 
    '18': 'Cher', '19': 'Corrèze', '2A': 'Corse-du-Sud', '2B': 'Haute-Corse', 
    '21': 'Côte-d\'Or', '22': 'Côtes-d\'Armor', '23': 'Creuse', '24': 'Dordogne', 
    '25': 'Doubs', '26': 'Drôme', '27': 'Eure', '28': 'Eure-et-Loir', '29': 'Finistère', 
    '30': 'Gard', '31': 'Haute-Garonne', '32': 'Gers', '33': 'Gironde', '34': 'Hérault', 
    '35': 'Ille-et-Vilaine', '36': 'Indre', '37': 'Indre-et-Loire', '38': 'Isère', 
    '39': 'Jura', '40': 'Landes', '41': 'Loir-et-Cher', '42': 'Loire', '43': 'Haute-Loire', 
    '44': 'Loire-Atlantique', '45': 'Loiret', '46': 'Lot', '47': 'Lot-et-Garonne', 
    '48': 'Lozère', '49': 'Maine-et-Loire', '50': 'Manche', '51': 'Marne', '52': 'Haute-Marne', 
    '53': 'Mayenne', '54': 'Meurthe-et-Moselle', '55': 'Meuse', '56': 'Morbihan', 
    '57': 'Moselle', '58': 'Nièvre', '59': 'Nord', '60': 'Oise', '61': 'Orne', 
    '62': 'Pas-de-Calais', '63': 'Puy-de-Dôme', '64': 'Pyrénées-Atlantiques', 
    '65': 'Hautes-Pyrénées', '66': 'Pyrénées-Orientales', '67': 'Bas-Rhin', '68': 'Haut-Rhin', 
    '69': 'Rhône', '70': 'Haute-Saône', '71': 'Saône-et-Loire', '72': 'Sarthe', 
    '73': 'Savoie', '74': 'Haute-Savoie', '75': 'Paris', '76': 'Seine-Maritime', 
    '77': 'Seine-et-Marne', '78': 'Yvelines', '79': 'Deux-Sèvres', '80': 'Somme', 
    '81': 'Tarn', '82': 'Tarn-et-Garonne', '83': 'Var', '84': 'Vaucluse', '85': 'Vendée', 
    '86': 'Vienne', '87': 'Haute-Vienne', '88': 'Vosges', '89': 'Yonne', '90': 'Territoire de Belfort', 
    '91': 'Essonne', '92': 'Hauts-de-Seine', '93': 'Seine-Saint-Denis', '94': 'Val-de-Marne', 
    '95': 'Val-d\'Oise', '971': 'Guadeloupe', '972': 'Martinique', '973': 'Guyane', 
    '974': 'La Réunion', '976': 'Mayotte'
}

def create_layout(dept_codes, types_biens, min_price, max_price):
    sidebar = html.Div(
        [
            html.Div([
                html.H2("ImmoViz", className="display-6"),
                html.Hr(),
            ], className="sidebar-header"),
            
            # Filtres
            html.Label("Département", className="filter-label"),
            dcc.Dropdown(
                id='filter-dept',
                options=[{'label': "France Entière", 'value': 'all'}] + 
                        [{'label': f"{d} - {DEPARTEMENTS.get(d, '')}", 'value': d} for d in dept_codes],
                value='all',
                clearable=False
            ),

            html.Label("Type de bien", className="filter-label"),
            dcc.Checklist(
                id='filter-type',
                options=[{'label': f" {t}", 'value': t} for t in types_biens],
                value=types_biens, # Tout coché par défaut
                inputStyle={"margin-right": "5px"},
                style={'color': '#ecf0f1'}
            ),

            html.Label("Date Début (2023)", className="filter-label"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id='start-day',
                    options=[{'label': i, 'value': i} for i in range(1, 32)],
                    value=1,
                    clearable=False,
                    placeholder="Jour"
                ), width=6),
                dbc.Col(dcc.Dropdown(
                    id='start-month',
                    options=[{'label': i, 'value': i} for i in range(1, 13)],
                    value=1,
                    clearable=False,
                    placeholder="Mois"
                ), width=6),
            ], className="mb-2"),

            html.Label("Date Fin (2023)", className="filter-label"),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id='end-day',
                    options=[{'label': i, 'value': i} for i in range(1, 32)],
                    value=31,
                    clearable=False,
                    placeholder="Jour"
                ), width=6),
                dbc.Col(dcc.Dropdown(
                    id='end-month',
                    options=[{'label': i, 'value': i} for i in range(1, 13)],
                    value=12,
                    clearable=False,
                    placeholder="Mois"
                ), width=6),
            ], className="mb-2"),

            
            html.Label("Prix / m² (€)", className="filter-label"),
            dcc.RangeSlider(
                id='filter-price',
                min=min_price,
                max=max_price,
                value=[min_price, max_price],
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            ),

            html.Label("Nb Ventes Min (Commune)", className="filter-label"),
            dcc.Input(
                id='filter-min-sales',
                type='number',
                value=2, # Default
                min=0,
                style={'width': '100%', 'margin-bottom': '1rem', 'color': 'black'}
            ),

            html.Button("Actualiser", id='btn-update', className="btn-update"),

            html.Div([
                html.Small("Modifiez les filtres puis cliquez sur Actualiser.", className="text-muted")
            ], style={'margin-top': '1rem'})
        ],
        className="sidebar"
    )

    content = html.Div(
        [
            # KPIs Row
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Prix Moyen"),
                    dbc.CardBody([
                        html.H2(id='kpi-price', className="kpi-value"),
                        html.Small("€ / m²", className="text-muted")
                    ])
                ]), width=12, md=3),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Volume Ventes"),
                    dbc.CardBody([
                        html.H2(id='kpi-volume', className="kpi-value"),
                        html.Small("Total période", className="text-muted")
                    ])
                ]), width=12, md=3),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Commune Top Prix"),
                    dbc.CardBody([
                        html.H4(id='kpi-top-city', className="kpi-value", style={'font-size': '1.2rem'}),
                        html.Small(id='kpi-top-price', className="text-muted")
                    ])
                ]), width=12, md=3),
                 dbc.Col(dbc.Card([
                    dbc.CardHeader("Surface Moyenne"),
                    dbc.CardBody([
                        html.H2(id='kpi-surface', className="kpi-value"),
                        html.Small("m²", className="text-muted")
                    ])
                ]), width=12, md=3),
            ], className="mb-4"),

            # Map Row
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Cartographie Interactive"),
                    dbc.CardBody([
                        dcc.Graph(id='map-graph', style={'height': '60vh'})
                    ], style={'padding': '0'})
                ], className="h-100"), width=12)
            ], className="mb-4"),

            # Charts Row 1
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Évolution Prix"),
                    dbc.CardBody(dcc.Graph(id='line-evol', style={'height': '300px'}))
                ]), width=12, md=8),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Répartition"),
                    dbc.CardBody(dcc.Graph(id='pie-type', style={'height': '300px'}))
                ]), width=12, md=4),
            ], className="mb-4"),

             # Charts Row 2
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Top 10 Villes (+chères)"),
                    dbc.CardBody(dcc.Graph(id='bar-top10', style={'height': '300px'}))
                ]), width=12, md=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Distribution Prix"),
                    dbc.CardBody(dcc.Graph(id='hist-dist', style={'height': '300px'}))
                ]), width=12, md=6),
            ]),
        ],
        className="content"
    )

    return html.Div([sidebar, content])
