# clean_data.py
import pandas as pd
import os

# Configuration
RAW_PATH = os.path.join("data", "raw", "dvf_2023.csv.gz")

CSV_DETAIL_PATH = os.path.join("data", "cleaned", "data_detail.csv")

# On traite par paquet de 100 000 lignes pour ne pas saturer la RAM
CHUNK_SIZE = 100000 

# --- FONCTION DE CORRECTION PLM ---
def fix_plm_codes(code):
    """
    Garde les codes des arrondissements pour afficher chaque arrondissement individuellement.
    Les codes PLM pour les arrondissements sont déjà valides dans GeoJSON.
    """
    code = str(code)
    # On ne modifie rien, on garde les codes originaux (y compris les arrondissements)
    return code

def process():
    print("Démarrage du traitement France Entière (CSV)...")
    


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