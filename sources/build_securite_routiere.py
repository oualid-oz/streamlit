"""Cas Sécurité routière: BAAC (accidents corporels), Loiret, 2019-2025, une ligne par accident."""

import io

import pandas as pd
import plotly.express as px
import requests
from common import BLUE, download, fr, record, save_figure, save_parquet, style

DATASET = "53698f4ca3a729239d2036df"  # "Bases de données annuelles des accidents corporels"
SOURCE = "https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2025/"
YEARS = range(2019, 2026)

resources = requests.get(f"https://www.data.gouv.fr/api/1/datasets/{DATASET}/", timeout=60).json()[
    "resources"
]


def load(kind, year):
    """kind: 'car' (caractéristiques), 'lieux' or 'usagers'. The spelling varies by year."""
    for r in resources:
        title = r["title"].lower()
        if str(year) in title and kind in title and r["format"] == "csv":
            df = pd.read_csv(
                io.BytesIO(download(r["url"])),
                sep=";",
                decimal=",",
                dtype={"dep": str, "com": str, "nbv": str},
            )
            df.columns = df.columns.str.lower()
            return df.rename(columns={"accident_id": "num_acc"})  # 2022 spells it differently
    raise ValueError(f"no {kind} file for {year}")


rows = []
for year in YEARS:
    carac = load("car", year)
    carac = carac[carac["dep"] == "45"]  # Loiret
    lieux = load("lieux", year)
    lieux = lieux.drop_duplicates("num_acc")  # since 2023, an accident on two roads has two rows
    usagers = load("usagers", year)
    usagers = usagers[usagers["num_acc"].isin(carac["num_acc"])]
    # grav: 1 indemne, 2 tué, 3 blessé hospitalisé, 4 blessé léger
    par_accident = usagers.groupby("num_acc").agg(
        nb_usagers=("grav", "size"),
        nb_tues=("grav", lambda g: (g == 2).sum()),
        nb_hospitalises=("grav", lambda g: (g == 3).sum()),
    )
    keep = ["num_acc", "catr", "surf", "vma", "circ", "nbv"]
    rows.append(
        carac.merge(lieux[keep], on="num_acc", how="left").merge(
            par_accident, on="num_acc", how="left"
        )
    )

df = pd.concat(rows, ignore_index=True)
for col in ["nbv", "vma", "surf", "catr"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["date"] = pd.to_datetime({"year": df["an"], "month": df["mois"], "day": df["jour"]})
df["heure"] = pd.to_numeric(df["hrmn"].str[:2])
df["grave"] = (df["nb_tues"] + df["nb_hospitalises"]) > 0

# Commune names (INSEE code -> name) from the official geo API.
communes = requests.get(
    "https://geo.api.gouv.fr/departements/45/communes?fields=nom,code", timeout=60
).json()
df["commune"] = df["com"].map({c["code"]: c["nom"] for c in communes})

# Readable labels for the codes used in the figures and in the drill-down.
labels = {
    "lum": {
        1: "Plein jour",
        2: "Crépuscule ou aube",
        3: "Nuit sans éclairage",
        4: "Nuit, éclairage éteint",
        5: "Nuit, éclairage allumé",
    },
    "atm": {
        1: "Normale",
        2: "Pluie légère",
        3: "Pluie forte",
        4: "Neige, grêle",
        5: "Brouillard",
        6: "Vent fort",
        7: "Éblouissant",
        8: "Couvert",
        9: "Autre",
    },
    "catr": {
        1: "Autoroute",
        2: "Route nationale",
        3: "Route départementale",
        4: "Voie communale",
        5: "Hors réseau public",
        6: "Parc de stationnement",
        7: "Route de métropole urbaine",
        9: "Autre",
    },
}
for col, mapping in labels.items():
    df[f"{col}_libelle"] = df[col].map(mapping)

df = df.drop(columns=["adr", "hrmn"]).sort_values(["date", "num_acc"]).reset_index(drop=True)
df = df.rename(columns={"num_acc": "id_accident"})
path = save_parquet(df, "securite_routiere")

# Starter figure: share of serious accidents (tué or hospitalisé) by road type.
par_route = (
    df.dropna(subset=["catr_libelle"])
    .groupby("catr_libelle")
    .agg(accidents=("grave", "size"), part_graves=("grave", "mean"))
    .query("accidents >= 100")
    .sort_values("part_graves")
    .reset_index()
)
par_route["part_graves"] *= 100
par_route["graves"] = (par_route["accidents"] * par_route["part_graves"] / 100).round().astype(int)
par_route = par_route.sort_values("graves")
taux = par_route.set_index("catr_libelle")
autoroute, dep = taux.loc["Autoroute"], taux.loc["Route départementale"]
# Le taux dit où c'est grave, le nombre dit où agir : on montre les deux.
title = (
    f"Sur autoroute, {autoroute['part_graves']:.0f} % des accidents sont graves. Les routes "
    f"départementales en comptent bien plus : {fr(int(dep['graves']))} contre {fr(int(autoroute['graves']))} "
    f"(n = {fr(len(df))} accidents, 2019-2025)"
)
fig = px.bar(
    par_route,
    x="graves",
    y="catr_libelle",
    orientation="h",
    text=[
        f"{g} graves sur {a} ({p:.0f} %)"
        for g, a, p in zip(par_route["graves"], par_route["accidents"], par_route["part_graves"])
    ],
    labels={"graves": "Accidents graves (tué ou hospitalisé)", "catr_libelle": ""},
)
fig.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False)
fig.update_xaxes(range=[0, par_route["graves"].max() * 1.95])
save_figure(style(fig, title), "securite_routiere")
record(
    "securite_routiere",
    df,
    path,
    "date",
    SOURCE,
    "Licence Ouverte v2.0 (Etalab)",
    title,
    note="grave = au moins un usager tué ou blessé hospitalisé (grav 2 ou 3)",
)
print(df.shape, title)
print(df["grave"].mean(), df["date"].min(), df["date"].max(), df["commune"].isna().sum())
