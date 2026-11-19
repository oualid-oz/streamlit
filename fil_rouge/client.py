"""Bonus de l'exo 5 : une appli Streamlit « et si ? » qui appelle POST /predict.

Question : et si je jouais plus tard, ou avec les noirs ?
À produire : un formulaire (couleur, cadence, écart d'Elo, heure), un requests.post vers /predict,
un st.metric, et un message lisible si l'API refuse la requête (422) ou ne répond pas.
Lancez api.py d'abord.
Lancer : uv run streamlit run fil_rouge/client.py --server.address 127.0.0.1
"""

import os

import requests  # noqa: F401
import streamlit as st

API = os.environ.get("AWP_API_URL", "http://127.0.0.1:8000")

st.title("Et si je jouais plus tard, ou avec les noirs ?")

# TODO 1. Un st.form avec les quatre champs et un bouton
# TODO 2. Au clic : requests.post(f"{API}/predict", json=..., timeout=10)
# TODO 3. st.metric de la probabilité, st.error si la réponse n'est pas un succès
