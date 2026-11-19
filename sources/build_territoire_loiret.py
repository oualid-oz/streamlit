"""Cas Territoire du Loiret: une ligne par commune, en jointant quatre petites sources.

- population municipale INSEE (données du Département du Loiret sur data.gouv.fr)
- structures de santé du Département (maisons de santé, centres médicaux...)
- lieux de covoiturage du Département
- centre de chaque commune (geo.api.gouv.fr), pour calculer la distance aux soins
"""

import io

import numpy as np
import pandas as pd
import plotly.express as px
import requests
from common import BLUE, VERMILLION, download, fr, record, save_figure, save_parquet, style

API = "https://www.data.gouv.fr/api/1/datasets"
POPULATION = "65b1a75befcf2cf78c5aa480"  # Population municipale des communes - Loiret
SANTE = "67c24e4de01c99c2b8a31a1f"  # Structures de santé - Département du Loiret
COVOITURAGE = "65a64a1be69e4163fc89ca45"  # Lieux de covoiturage - Département du Loiret
SOURCE = "https://www.data.gouv.fr/organizations/departement-du-loiret/"


def read_dataset(dataset_id, formats):
    """Read the first resource of the dataset (in these formats) whose link still works."""
    for resource in requests.get(f"{API}/{dataset_id}/", timeout=60).json()["resources"]:
        if resource["format"] not in formats:
            continue
        try:
            content = download(resource["url"])
        except requests.RequestException:
            continue  # some links of the Département are dead (404)
        if resource["format"] == "csv":
            return pd.read_csv(io.BytesIO(content), dtype=str)
        return pd.read_excel(io.BytesIO(content), dtype={"codgeo": str, "code_insee": str})
    raise ValueError(f"no working resource for {dataset_id}")


pop = read_dataset(POPULATION, {"xls"})
pop = pop.rename(columns={"codgeo": "code_insee", "libgeo": "commune", "cv": "canton",
                          "superf": "superficie_km2"})  # fmt: skip
pop = pop[["code_insee", "commune", "arr", "canton", "superficie_km2", "p14_pop", "p23_pop"]]
pop = pop.rename(columns={"p14_pop": "population_2014", "p23_pop": "population_2023"})

# Centre of each commune: needed to measure the distance to the nearest health structure.
geo = requests.get(
    "https://geo.api.gouv.fr/departements/45/communes?fields=code,centre", timeout=60
).json()
centres = pd.DataFrame(
    {"code_insee": c["code"], "lon": c["centre"]["coordinates"][0],
     "lat": c["centre"]["coordinates"][1]} for c in geo
)  # fmt: skip
df = pop.merge(centres, on="code_insee", how="left")

sante = read_dataset(SANTE, {"xls"})
covoit = read_dataset(COVOITURAGE, {"csv"})
covoit["nbre_pl"] = pd.to_numeric(covoit["nbre_pl"]).fillna(0)

# Counts per commune (communes without any equipment get 0, not NaN).
par_commune = pd.DataFrame(
    {
        "nb_structures_sante": sante.groupby("code_insee").size(),
        "nb_msp": sante[sante["type_struc"].str.contains("MSP", na=False)]
        .groupby("code_insee").size(),
        "nb_lieux_covoiturage": covoit.groupby("insee").size(),
        "places_covoiturage": covoit.groupby("insee")["nbre_pl"].sum(),
    }
)  # fmt: skip
df = df.merge(par_commune, left_on="code_insee", right_index=True, how="left")
for col in par_commune.columns:
    df[col] = df[col].fillna(0).astype(int)


def distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance (haversine), in km. Arrays broadcast against each other."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371 * np.arcsin(np.sqrt(a))


# Distance from each commune centre to the nearest health structure (communes x structures).
dist = distance_km(
    df[["lat"]].to_numpy(), df[["lon"]].to_numpy(),
    sante["latitude"].to_numpy()[None, :], sante["longitude"].to_numpy()[None, :],
)  # fmt: skip
df["distance_soins_km"] = dist.min(axis=1).round(1)
df["densite_hab_km2"] = (df["population_2023"] / df["superficie_km2"]).round(1)
df = df.sort_values("population_2023", ascending=False).reset_index(drop=True)
path = save_parquet(df, "territoire_loiret")

# Starter figure: how far from a health structure do the inhabitants live?
df["tranche"] = pd.cut(df["distance_soins_km"], [-0.1, 2, 5, 10, 100],
                       labels=["moins de 2 km", "2 à 5 km", "5 à 10 km", "plus de 10 km"])  # fmt: skip
par_tranche = df.groupby("tranche", observed=True).agg(
    communes=("code_insee", "size"), habitants=("population_2023", "sum")
).reset_index()  # fmt: skip
loin = df[df["distance_soins_km"] > 10]
title = (
    f"{fr(int(loin['population_2023'].sum()))} habitants ({len(loin)} communes) vivent à plus de "
    f"10 km d'une structure de santé du Département (n = {len(df)} communes, "
    f"{fr(int(df['population_2023'].sum()))} habitants en 2023)"
)
fig = px.bar(
    par_tranche, x="tranche", y="habitants",
    text=par_tranche["habitants"].map(lambda n: fr(int(n))),
    labels={"tranche": "Distance au plus proche établissement de santé (à vol d'oiseau)",
            "habitants": "Habitants en 2023"},
)  # fmt: skip
fig.update_traces(marker_color=[BLUE, BLUE, BLUE, VERMILLION])
save_figure(style(fig, title), "territoire_loiret")
df = df.drop(columns="tranche")
record(
    "territoire_loiret", df, path, None, SOURCE, "Licence Ouverte v2.0 (Etalab)", title,
    note=f"population municipale INSEE {df['population_2023'].size} communes (recensement 2023); "
    f"{len(sante)} structures de santé et {len(covoit)} lieux de covoiturage; "
    "canton = code INSEE du canton-ville (pas de libellé dans la source)",
    period_note="population 2014-2023; structures de santé mises à jour oct. 2025; "
    "covoiturage mis à jour janv. 2024",
)  # fmt: skip
print(df.shape, title)
print(df[["nb_structures_sante", "nb_lieux_covoiturage"]].sum().to_dict(), df.isna().sum().sum())
