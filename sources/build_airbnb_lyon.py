"""Cas Location courte durée: Inside Airbnb Lyon (annonces + échantillon d'avis)."""

import re

import plotly.express as px
from common import BLUE, VERMILLION, fr, read_csv, record, save_figure, save_parquet, style

BASE = "https://data.insideairbnb.com/france/auvergne-rhone-alpes/lyon/2026-09-17/data"
SOURCE = "https://insideairbnb.com/get-the-data/"

listings = read_csv(f"{BASE}/listings.csv.gz", low_memory=False)  # NOT calendar.csv.gz

# Keep what a pricing decision needs. Host names, host ids and URLs are left out.
df = listings.rename(
    columns={
        "id": "id_annonce",
        "neighbourhood_cleansed": "quartier",
        "price_quote_price_per_night": "prix_nuit",
        "name": "titre",
    }
)[
    [
        "id_annonce", "titre", "quartier", "latitude", "longitude", "property_type", "room_type",
        "accommodates", "bedrooms", "beds", "prix_nuit", "minimum_nights", "availability_365",
        "number_of_reviews", "number_of_reviews_ltm", "review_scores_rating",
        "review_scores_location", "review_scores_value", "host_is_superhost", "instant_bookable",
        "estimated_occupancy_l365d", "estimated_revenue_l365d", "first_review", "last_review",
        "last_scraped",
    ]
]  # fmt: skip
# `price` is only filled when Inside Airbnb obtained a price quote (5 069 of 9 201 listings);
# prix_nuit is NaN for the others.
path = save_parquet(df, "airbnb_lyon")

# Reviews: a random sample of 20 000 (the full file is ~47 MB compressed). No reviewer name or id.
reviews = read_csv(f"{BASE}/reviews.csv.gz", usecols=["listing_id", "date", "comments"])
reviews = reviews.dropna(subset=["comments"]).sample(20_000, random_state=0).sort_values("date")

# Les avis citent souvent l'hôte par son prénom. On remplace le host_name de chaque annonce,
# puis une seconde passe sur « merci X », « chez X », « thanks X ».
hotes = listings.set_index("id")["host_name"].dropna().astype(str)
APRES = re.compile(r"\b((?i:merci|thanks|thank you|host|hôte|chez)\s+)([A-ZÉ][a-zé]+)")


def sans_prenom(listing_id, texte):
    for nom in re.split(r"\s*(?:&|,|\bet\b|\band\b)\s*", hotes.get(listing_id, "")):
        if len(nom) > 1:
            texte = re.sub(rf"\b{re.escape(nom)}\b", "[hôte]", texte)
    return APRES.sub(
        lambda m: m.group(0) if m.group(2) == "France" else m.group(1) + "[hôte]", texte
    )


reviews["comments"] = [
    sans_prenom(i, t) for i, t in zip(reviews["listing_id"], reviews["comments"])
]
reviews_path = save_parquet(reviews.reset_index(drop=True), "airbnb_lyon_reviews")

# Starter figure: median nightly price by arrondissement, listings with a price only.
priced = df.dropna(subset=["prix_nuit"])
par_quartier = (
    priced.groupby("quartier")
    .agg(annonces=("prix_nuit", "size"), prix_median=("prix_nuit", "median"))
    .sort_values("prix_median")
    .reset_index()
)
bas, haut = par_quartier.iloc[0], par_quartier.iloc[-1]
title = (
    f"Le prix médian par nuit va de {bas['prix_median']:.0f} ({bas['quartier']}) "
    f"à {haut['prix_median']:.0f} ({haut['quartier']}) "
    f"(n = {fr(len(priced))} annonces avec prix, Lyon, septembre 2026)"
)
fig = px.bar(
    par_quartier,
    x="prix_median",
    y="quartier",
    orientation="h",
    text=par_quartier["prix_median"].round(0).astype(int),
    labels={"prix_median": "Prix médian par nuit (montant publié)", "quartier": ""},
)
fig.update_traces(marker_color=[BLUE] * (len(par_quartier) - 1) + [VERMILLION])
save_figure(style(fig, title), "airbnb_lyon")
record(
    "airbnb_lyon", df, path, "last_scraped", SOURCE, "Creative Commons Attribution 4.0 (CC BY 4.0)",
    title,
    note=f"prix_nuit renseigné pour {len(priced)} annonces sur {len(df)}; le fichier source écrit "
    "le prix avec un symbole $ sans préciser la devise",
    reviews_sample={
        "file": reviews_path.name,
        "rows": len(reviews),
        "columns": list(reviews.columns),
        "period": [str(reviews["date"].min()), str(reviews["date"].max())],
        "size_mb": round(reviews_path.stat().st_size / 1e6, 2),
    },
)  # fmt: skip
print(df.shape, reviews.shape, title)
