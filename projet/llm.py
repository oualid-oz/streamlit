"""Un client LLM compatible OpenAI. Adresse, clé et modèle viennent de .streamlit/secrets.toml."""

import re

import streamlit as st
from openai import OpenAI

client = OpenAI(base_url=st.secrets["LLM_URL"], api_key=st.secrets["LLM_KEY"])


@st.cache_data(ttl=3600)  # même agrégat, même réponse, pas de nouvel appel
def resumer(
    agregat: str,
    consigne: str = "Résume ce tableau en 3 phrases, en français, sans inventer de chiffre.",
) -> str:
    r = client.chat.completions.create(
        model=st.secrets["LLM_MODEL"],
        temperature=0,
        messages=[{"role": "system", "content": consigne}, {"role": "user", "content": agregat}],
    )
    return re.sub(r"<think>.*?</think>", "", r.choices[0].message.content, flags=re.DOTALL).strip()
