"""Exo 1 : trois figures. Environ 25 min.

Question : où ce joueur perd-il des points ?
À produire : trois figures Plotly dont le titre dit ce qu'elles montrent.
Lancer : uv run python fil_rouge/01_figures.py
"""

import plotly.express as px

from data import familles, load_coups, load_data

df, coups = load_data(), load_coups()
print(df.shape, coups.shape)

# 1. Le score par famille d'ouvertures, la pire en haut (px.bar, familles(df))
f = familles(df)
fig1 = px.bar(
    f,
    x="score",
    y="famille",
    orientation="h",
    hover_data=["n", "gaffes"],
    title=f"{f['famille'].iloc[0]} est mon ouverture la moins rentable (score moyen, 30 parties ou plus)",
)
fig1.update_yaxes(autorange="reversed", title=None)  # la pire en haut
fig1.update_xaxes(range=[0, 1], title="score moyen (1 = victoire, 0,5 = nulle)")
fig1.show()

# 2. La phase de la partie où tombent ses gaffes : ouverture, milieu, finale (coups)
phases = {"opening": "ouverture", "middlegame": "milieu de jeu", "endgame": "finale"}
g = (
    coups[coups["jugement"] == "blunder"]["phase"]
    .map(phases)
    .value_counts()
    .reindex(list(phases.values()))
    .rename_axis("phase")
    .reset_index(name="gaffes")
)
pire = g.loc[g["gaffes"].idxmax(), "phase"]
fig2 = px.bar(g, x="phase", y="gaffes", title=f"La plupart de mes gaffes tombent en {pire}")
fig2.show()

# 3. Le score selon l'heure de la partie (heures UTC, au moins 30 parties par heure)
h = df.groupby("heure").agg(n=("partie_id", "nunique"), score=("score", "mean")).reset_index()
h = h[h["n"] >= 30]
fig3 = px.line(
    h,
    x="heure",
    y="score",
    markers=True,
    hover_data=["n"],
    title="Mon score selon l'heure de la partie (UTC, heures avec 30 parties ou plus)",
)
fig3.update_xaxes(dtick=1, title="heure (UTC)")
fig3.update_yaxes(title="score moyen")
fig3.show()
