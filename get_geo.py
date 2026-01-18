# get_geo.py
import requests
import os

# Fichier GeoJSON des communes de France (Optimisé 100Mo)
GEO_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"
OUTPUT_DIR = os.path.join("data", "raw")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "communes.geojson")

def get_geojson():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Téléchargement de la carte de France...")
    try:
        r = requests.get(GEO_URL, stream=True)
        with open(OUTPUT_PATH, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
        print("GeoJSON France téléchargé.")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    get_geojson()