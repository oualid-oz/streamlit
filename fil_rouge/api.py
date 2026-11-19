"""Exo 5 : le service FastAPI. Environ 45 min.

Question : mes parties derrière une API que n'importe quel client peut appeler (votre appli, puis l'agent de l'exo 6).
À produire : GET /ouvertures et GET /parties, paramètres validés (une cadence inconnue renvoie 422, pas une liste vide).
Ensuite : app_api.py, ou votre appli de l'exo 2 ou de l'exo 4, appelle cette API au lieu de lire les CSV.
Bonus : POST /predict avec le modèle fourni (fil_rouge/model.joblib, déjà entraîné), puis client.py.
Lancer : uv run uvicorn api:app --app-dir fil_rouge --host 127.0.0.1 --port 8000 --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from data import familles, load_data  # noqa: F401

app = FastAPI(title="Mes parties d'échecs", version="1.0")

# TODO 1. Charger les données une fois, au démarrage : df = load_data()
# TODO 2. GET /ouvertures : cadence facultative (bullet, blitz ou rapid, avec Literal), min_n >= 1 ;
#         les familles, la pire d'abord (familles de data.py)
# TODO 3. GET /parties : cadence et couleur facultatives, limit entre 1 et 500 (Query)
# Bonus. joblib.load(Path(__file__).parent / "model.joblib"), une classe Partie(BaseModel)
#        (couleur, cadence, ecart_elo, heure de 0 à 23), POST /predict qui renvoie {"proba_victoire": ...}
