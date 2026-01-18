# process_data.py
import pandas as pd
import os

# Configuration
RAW_PATH = os.path.join("data", "raw", "dvf_2023.csv.gz")
CSV_MAP_PATH = os.path.join("data", "cleaned", "data_map.csv")
CSV_DETAIL_PATH = os.path.join("data", "cleaned", "data_detail.csv")

# On traite par paquet de 100 000 lignes pour ne pas saturer la RAM
CHUNK_SIZE = 100000 

# --- FONCTION DE CORRECTION PLM ---
def fix_plm_codes(code):
    """
    Transforme les arrondissements en la commune principale.
    Ex: 75112 -> 75056 (Paris)
    """
    code = str(code)
    if code.startswith('751'): return '75056' # Paris
    if code.startswith('132'): return '13055' # Marseille
    if code.startswith('693'): return '69123' # Lyon
    return code

def process():
    print("Démarrage du traitement France Entière (CSV)...")
    
    if not os.path.exists(os.path.dirname(CSV_MAP_PATH)):
        os.makedirs(os.path.dirname(CSV_MAP_PATH))

    # Colonnes strictement nécessaires
    cols = ['date_mutation', 'nature_mutation', 'valeur_fonciere', 
            'code_departement', 'code_commune', 'nom_commune', 
            'type_local', 'surface_reelle_bati']

    # Listes pour stocker les résultats temporaires
    chunks_kept = []

    # Lecture du fichier compressé par morceaux
    reader = pd.read_csv(RAW_PATH, compression='gzip', usecols=cols, 
                         dtype={'code_commune': str, 'code_departement': str}, 
                         chunksize=CHUNK_SIZE)

    total_rows = 0
    
    for i, chunk in enumerate(reader):
        # 1. Filtrage initial (rapide)
        chunk = chunk[chunk['nature_mutation'] == "Vente"]
        chunk = chunk[chunk['type_local'].isin(['Maison', 'Appartement'])]
        chunk = chunk.dropna(subset=['valeur_fonciere', 'surface_reelle_bati', 'code_commune'])
        chunk = chunk[chunk['surface_reelle_bati'] > 9]
        chunk = chunk[chunk['valeur_fonciere'] > 1000]

        # 2. Correction des codes communes PLM
        chunk['code_commune'] = chunk['code_commune'].apply(fix_plm_codes)

        # 3. Calculs
        chunk['prix_m2'] = chunk['valeur_fonciere'] / chunk['surface_reelle_bati']
        # Filtre des prix aberrants
        chunk = chunk[(chunk['prix_m2'] > 500) & (chunk['prix_m2'] < 25000)]
        
        # Ajout à la liste
        chunks_kept.append(chunk)
        
        total_rows += len(chunk)
        print(f"   Traitement lot {i}... ({total_rows} ventes conservées)")

    print("Fusion des données...")
    df = pd.concat(chunks_kept)
    
    # --- FICHIER 1 : POUR LA CARTE (Agrégation par ville) ---
    print("Création du fichier CARTE (Moyenne par ville)...")
    df_map = df.groupby(['code_commune', 'nom_commune', 'code_departement'])['prix_m2'].agg(['mean', 'count']).reset_index()
    df_map.columns = ['code_commune', 'nom_commune', 'code_departement', 'prix_moyen', 'nb_ventes']
    # On garde seulement les villes avec > 5 ventes pour la carte
    df_map = df_map[df_map['nb_ventes'] > 5]
    df_map.to_csv(CSV_MAP_PATH, index=False)
    print(f"{CSV_MAP_PATH} généré.")

    # --- FICHIER 2 : DONNÉES DÉTAILLÉES (Pour les graphs) ---
    # Pour que le CSV ne fasse pas 2 Go, on ne garde que l'essentiel pour les stats
    # On ajoute le mois pour l'évolution temporelle
    print("Création du fichier DÉTAIL...")
    df['date_mutation'] = pd.to_datetime(df['date_mutation'])
    df['mois'] = df['date_mutation'].dt.to_period('M').astype(str)
    
    # On sauvegarde tout (Attention, le fichier sera gros)
    df.to_csv(CSV_DETAIL_PATH, index=False)
    print(f"{CSV_DETAIL_PATH} généré.")
    print("Terminé.")

if __name__ == "__main__":
    process()