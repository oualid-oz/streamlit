"""Cas Immobilier: DVF géolocalisé, Loiret, ventes d'appartements et de maisons 2021-2025."""

import gzip
import io

import pandas as pd
import plotly.express as px
from common import BLUE, ORANGE, download, fr, record, save_figure, save_parquet, style

URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/45.csv.gz"
SOURCE = "https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/"
YEARS = range(2021, 2026)

raw = pd.concat(
    pd.read_csv(io.BytesIO(gzip.decompress(download(URL.format(year=y)))), dtype=str) for y in YEARS
)
print("lignes DVF brutes :", len(raw))

# One DVF row = one parcel (and land type) of one mutation. Work on sales only.
sales = raw[raw["nature_mutation"] == "Vente"].copy()
for col in ["valeur_fonciere", "surface_reelle_bati", "nombre_pieces_principales"]:
    sales[col] = pd.to_numeric(sales[col])
for col in ["surface_terrain", "longitude", "latitude"]:
    sales[col] = pd.to_numeric(sales[col])

# Land of each mutation: sum of its distinct parcel/land-type rows.
terrain = (
    sales.drop_duplicates(["id_mutation", "id_parcelle", "code_nature_culture", "surface_terrain"])
    .groupby("id_mutation")["surface_terrain"]
    .sum()
)

# Keep flats and houses. The same dwelling is repeated once per land row: drop those copies.
df = sales[sales["type_local"].isin(["Appartement", "Maison"])]
df = df.drop_duplicates(
    ["id_mutation", "type_local", "surface_reelle_bati", "nombre_pieces_principales"]
)
# A mutation with several dwellings has ONE price for all of them: keep single-dwelling sales,
# otherwise price per m2 would be wrong.
df = df[~df["id_mutation"].duplicated(keep=False)].copy()
df["surface_terrain"] = df["id_mutation"].map(terrain)

# Drop obvious data errors: symbolic prices, absurd surfaces, absurd prices per m2.
df = df.assign(prix_m2=df["valeur_fonciere"] / df["surface_reelle_bati"])
df = df[
    df["valeur_fonciere"].between(10_000, 2_000_000)
    & df["surface_reelle_bati"].between(9, 400)
    & df["prix_m2"].between(300, 8_000)
]

df = df.assign(
    date_mutation=pd.to_datetime(df["date_mutation"]),
    section=df["id_parcelle"].str[8:10],  # "45234000AB0012" -> section "AB"
    annee=pd.to_datetime(df["date_mutation"]).dt.year,
)
df = (
    df.rename(columns={"type_local": "type"})[
        [
            "id_mutation",
            "date_mutation",
            "annee",
            "valeur_fonciere",
            "type",
            "surface_reelle_bati",
            "nombre_pieces_principales",
            "prix_m2",
            "surface_terrain",
            "code_commune",
            "nom_commune",
            "code_postal",
            "section",
            "longitude",
            "latitude",
        ]
    ]
    .sort_values("date_mutation")
    .reset_index(drop=True)
)  # no street address kept
path = save_parquet(df, "immobilier")

# Starter figure: median price per m2 per year, Orléans against the rest of the Loiret.
df["zone"] = df["nom_commune"].eq("Orléans").map({True: "Orléans", False: "Reste du Loiret"})
par_an = df.groupby(["annee", "zone"], as_index=False)["prix_m2"].median()
orleans = df[df["zone"] == "Orléans"]
title = (
    f"À Orléans, le prix médian est de {fr(round(orleans['prix_m2'].median()))} €/m² "
    f"contre {fr(round(df[df['zone'] != 'Orléans']['prix_m2'].median()))} € ailleurs dans le Loiret "
    f"(n = {fr(len(df))} ventes, dont {fr(len(orleans))} à Orléans, 2021-2025)"
)
fig = px.line(
    par_an,
    x="annee",
    y="prix_m2",
    color="zone",
    markers=True,
    color_discrete_map={"Orléans": BLUE, "Reste du Loiret": ORANGE},
    labels={"annee": "Année de la vente", "prix_m2": "Prix médian (€/m²)"},
)
fig.update_xaxes(dtick=1)
save_figure(style(fig, title), "immobilier")
df = df.drop(columns="zone")
record(
    "immobilier", df, path, "date_mutation", SOURCE, "Licence Ouverte v2.0 (Etalab)", title,
    note="ventes d'un seul logement (une mutation = une ligne), prix 10 k-2 M euros, "
    "9-400 m2, 300-8000 euros/m2",
)  # fmt: skip
print(df.shape, title)
