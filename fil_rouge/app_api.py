"""Exo 5, suite : l'appli ne lit plus les CSV, elle demande à l'API. Environ 45 min.

Question : la même appli qu'à l'exo 2, mais ses chiffres viennent de l'API.
À produire : une barre latérale (cadence, parties minimum), la figure des familles depuis GET /ouvertures,
les dix dernières parties depuis GET /parties, et un message lisible si l'API ne répond pas.
Vous pouvez aussi modifier directement votre app_streamlit.py ou votre app_dash.py.
Lancez api.py d'abord.
Lancer : uv run streamlit run fil_rouge/app_api.py --server.address 127.0.0.1
"""

import os

import requests  # noqa: F401
import streamlit as st

API = os.environ.get("AWP_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Mes parties d'échecs", layout="wide")
st.title("Quelles ouvertures me coûtent des points\u00a0?")

# TODO 1. Une fonction appeler(chemin, **params) : requests.get(f"{API}{chemin}", params=params, timeout=10),
#         r.raise_for_status(), puis un DataFrame de r.json()
# TODO 2. La barre latérale : cadence (blitz, rapid, bullet) et parties minimum par ouverture
# TODO 3. GET /ouvertures : la figure des familles (barres horizontales, la pire en haut)
# TODO 4. GET /parties : st.dataframe des dix dernières parties
# TODO 5. API arrêtée : st.error et st.stop, pas une trace (except requests.RequestException)
