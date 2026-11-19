"""Vendredi : le point de départ de votre appli.

Lancer : uv run streamlit run projet/app.py --server.address 127.0.0.1
"""

from pathlib import Path

import pandas as pd
import plotly.express as px  # noqa: F401
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "projets"
CAS = "immobilier"  # old_veloroutes, colleges_risques, energie, securite_routiere, immobilier, airbnb_lyon, olist, territoire_loiret


@st.cache_data
def charger(cas: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{cas}.parquet")


df = charger(CAS)
st.title("Le titre dit la décision")
st.caption(f"{len(df):,} lignes, {df.shape[1]} colonnes".replace(",", " "))
st.dataframe(df.head(20))
