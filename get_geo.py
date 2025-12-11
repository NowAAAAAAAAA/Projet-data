# get_geo.py
import requests
import os

# URL du GeoJSON des communes de France (simplifié pour le web)
GEO_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"
OUTPUT_DIR = os.path.join("data", "raw")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "communes.geojson")

def get_geojson():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if os.path.exists(OUTPUT_PATH):
        print("✅ GeoJSON déjà présent.")
        return

    print("⬇️ Téléchargement du fond de carte des communes (c'est un gros fichier ~100Mo)...")
    r = requests.get(GEO_URL)
    with open(OUTPUT_PATH, 'wb') as f:
        f.write(r.content)
    print("✅ GeoJSON téléchargé.")

if __name__ == "__main__":
    get_geojson()