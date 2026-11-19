"""Cas Énergie: éCO2mix régional, Centre-Val de Loire, demi-heures depuis septembre 2023."""

import io

import pandas as pd
import plotly.express as px
from common import (
    BLUE,
    ORANGE,
    download,
    fr,
    record,
    save_figure,
    save_parquet,
    style,
)

API = "https://opendata.reseaux-energies.fr/api/explore/v2.1/catalog/datasets"
DATASET = "eco2mix-regional-cons-def"
SOURCE = f"https://opendata.reseaux-energies.fr/explore/dataset/{DATASET}/"

# Centre-Val de Loire = région 24. The API filters server-side, so only ~50 000 rows come down.
raw = download(
    f"{API}/{DATASET}/exports/csv",
    where="code_insee_region=\"24\" and date_heure>=date'2023-09-01'",
    delimiter=";",
    select=(
        "date_heure,nature,consommation,thermique,nucleaire,eolien,solaire,"
        "hydraulique,bioenergies,pompage,ech_physiques"
    ),
)
df = pd.read_csv(io.BytesIO(raw), sep=";", parse_dates=["date_heure"])
df = df.sort_values("date_heure").reset_index(drop=True)

# Local time (Paris) is what an energy buyer reasons in; date_heure stays in UTC.
local = df["date_heure"].dt.tz_convert("Europe/Paris")
df["date"] = local.dt.date.astype("datetime64[s]")
df["heure"] = local.dt.hour + local.dt.minute / 60
df["jour_semaine"] = local.dt.day_of_week  # 0 = lundi
df["type_jour"] = df["jour_semaine"].map(lambda d: "week-end" if d >= 5 else "semaine")
df = df.dropna(subset=["consommation"])
path = save_parquet(df, "energie")

# Starter figure: the average day, weekday against weekend.
profil = df.groupby(["heure", "type_jour"], as_index=False)["consommation"].mean()
semaine = profil[profil["type_jour"] == "semaine"].set_index("heure")["consommation"]


def hhmm(h):
    return f"{int(h)} h {int(h % 1 * 60):02d}"


creux, pic = hhmm(semaine.idxmin()), hhmm(semaine.idxmax())
title = (
    f"En semaine, la consommation passe de {semaine.min():.0f} MW à {creux} "
    f"à {semaine.max():.0f} MW à {pic} (n = {fr(len(df))} demi-heures, "
    f"{df['date'].min():%m/%Y} à {df['date'].max():%m/%Y})"
)
fig = px.line(
    profil,
    x="heure",
    y="consommation",
    color="type_jour",
    color_discrete_map={"semaine": BLUE, "week-end": ORANGE},
    labels={"heure": "Heure locale", "consommation": "Consommation moyenne (MW)"},
)
save_figure(style(fig, title), "energie")
record("energie", df, path, "date", SOURCE, "Licence Ouverte v2.0 (Etalab)", title)
print(df.shape, title)
