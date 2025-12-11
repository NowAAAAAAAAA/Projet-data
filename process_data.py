# process_data.py
import pandas as pd
import os

# Configuration
RAW_PATH = os.path.join("data", "raw", "dvf_2023.csv.gz")
CLEAN_PATH = os.path.join("data", "cleaned", "dvf_idf.parquet")
AGG_PATH = os.path.join("data", "cleaned", "stats_communes.parquet")

DEPARTEMENTS_IDF = ['75', '77', '78', '91', '92', '93', '94', '95']

def process():
    print("🔄 Chargement des données brutes...")
    cols = ['date_mutation', 'nature_mutation', 'valeur_fonciere', 
            'code_departement', 'code_commune', 'nom_commune', 
            'type_local', 'surface_reelle_bati']
    
    # On force les codes en string pour éviter de perdre le '0' au début (ex: 01)
    df = pd.read_csv(RAW_PATH, compression='gzip', usecols=cols, 
                     dtype={'code_commune': str, 'code_departement': str})

    # 1. Filtre IDF
    print("📍 Filtrage Île-de-France...")
    df = df[df['code_departement'].isin(DEPARTEMENTS_IDF)]
    
    # 2. Nettoyage classique
    df = df[df['nature_mutation'] == "Vente"]
    df = df[df['type_local'].isin(['Maison', 'Appartement'])]
    df = df.dropna(subset=['valeur_fonciere', 'surface_reelle_bati'])
    df = df[df['surface_reelle_bati'] > 9]
    df = df[df['valeur_fonciere'] > 1000]

    # 3. Calcul Prix m2
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
    # Suppression des extrêmes (erreurs de saisie fréquentes)
    df = df[(df['prix_m2'] > 1000) & (df['prix_m2'] < 40000)]

    # 4. Sauvegarde des données détaillées
    if not os.path.exists(os.path.dirname(CLEAN_PATH)):
        os.makedirs(os.path.dirname(CLEAN_PATH))
    df.to_parquet(CLEAN_PATH)
    print(f"💾 Données détaillées sauvegardées : {len(df)} ventes.")

    # 5. Création du fichier AGGRÉGÉ pour la carte (Une ligne par ville)
    print("📊 Calcul des moyennes par ville...")
    df_agg = df.groupby(['code_commune', 'nom_commune'])['prix_m2'].agg(['mean', 'count']).reset_index()
    df_agg.columns = ['code_commune', 'nom_commune', 'prix_moyen', 'nb_ventes']
    # On garde seulement les villes avec assez de ventes pour que la stats soit fiable
    df_agg = df_agg[df_agg['nb_ventes'] > 10]
    
    df_agg.to_parquet(AGG_PATH)
    print("💾 Stats par commune sauvegardées.")

if __name__ == "__main__":
    process()