"""Cas Collèges du Loiret: une ligne par collège et par rentrée, en jointant le code UAI.

- collèges publics et privés + secteurs de recrutement (GéoLoiret, Département du Loiret)
- effectifs par niveau (data.education.gouv.fr, rentrées 2019 à 2025)
- indice de position sociale, IPS (data.education.gouv.fr, trois jeux mis bout à bout, 2016 à 2025)
- réussite au brevet: DNB par établissement (sessions jusqu'en 2021) puis indicateurs de
  valeur ajoutée des collèges (IVAC, sessions 2022 à 2025)

Sorties: colleges.parquet (pandas seulement) et colleges_secteurs.geojson (plotly, sans geopandas).
"""

import json
import re

import pandas as pd
import plotly.graph_objects as go
from common import BLUE, DATA, VERMILLION, download, fr, record, save_figure, save_parquet, style
from shapely.geometry import mapping, shape

GEO = "https://geoloiret.loiret-numerique.fr/ags25/rest/services"
COLLEGES_URL = f"{GEO}/III_2_Batiment/ETABLISSEMENTS_SCOLAIRES/FeatureServer/4"
SECTEURS_URL = f"{GEO}/III_11_Zones_Gestion/SECTORISATION_EDUCATION/FeatureServer/3"
ODS = "https://data.education.gouv.fr/api/v2/catalog/datasets"
EFFECTIFS = "fr-en-college-effectifs-niveau-sexe-lv"
IPS = ["fr-en-ips_colleges", "fr-en-ips-colleges-ap2022", "fr-en-ips-colleges-ap2023"]
DNB = "fr-en-dnb-par-etablissement"
IVAC = "fr-en-indicateurs-valeur-ajoutee-colleges"
CATALOGUE = "https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm"
SIMPLIFY_DEG = 0.0001  # ~ 10 m: assez fin pour une carte départementale, sous les 3 Mo


def arcgis(layer_url):
    """All features of an ArcGIS FeatureServer layer as GeoJSON (WGS84), paginated."""
    features, offset = [], 0
    while True:
        page = json.loads(download(
            f"{layer_url}/query", where="1=1", outFields="*", outSR=4326, f="geojson",
            resultOffset=offset, resultRecordCount=1000, orderByFields="objectid",
        ))  # fmt: skip
        features += page["features"]
        if len(page["features"]) < 1000:
            return features
        offset += 1000


def ods(dataset_id, where):
    """All records of an Opendatasoft v2.1 dataset matching `where`, as a DataFrame."""
    rows, offset = [], 0
    while True:
        page = json.loads(download(
            f"{ODS}/{dataset_id}/records", where=where, limit=100, offset=offset
        ))  # fmt: skip
        rows += [r["record"]["fields"] for r in page["records"]]
        if len(page["records"]) < 100:
            return pd.DataFrame(rows)
        offset += 100


# --- 1. Collèges (GéoLoiret): 70 points, clé = UAI -------------------------------------------
pts = arcgis(COLLEGES_URL)
base = pd.DataFrame(
    {
        "uai": f["properties"]["identifiant"],
        "nom": f["properties"]["nom"].removeprefix("Collège ").strip(),
        "commune": f["properties"]["commune"],
        "code_insee": f["properties"]["code_insee"],
        "statut": "privé" if f["properties"]["type"].endswith("Privé") else "public",
        "lat": round(f["geometry"]["coordinates"][1], 5),
        "lon": round(f["geometry"]["coordinates"][0], 5),
    }
    for f in pts
)  # fmt: skip
assert base["uai"].is_unique and len(base) == 70, "GéoLoiret: 70 collèges attendus"

# --- 2. Secteurs (GéoLoiret): lien secteur -> collège par le code UAI (clg_rne) ---------------
polys = arcgis(SECTEURS_URL)
secteurs_raw = pd.DataFrame([f["properties"] for f in polys])
polysecteur = secteurs_raw[secteurs_raw["clg_rne"].str.len() != 8]  # un code à 7 caractères
secteur_par_uai = dict(zip(secteurs_raw["clg_rne"], secteurs_raw["clg_rne"]))
# Polysecteur de La Source: un seul polygone pour deux collèges (Montesquieu et Alain Fournier).
for _, ps in polysecteur.iterrows():
    for nom in re.findall(r"Collèges (.+)", ps["clg_sec"])[0].split(" & "):
        hit = base["nom"].str.contains(nom.strip(), case=False, regex=False)
        for uai in base.loc[hit & (base["commune"] == "Orléans"), "uai"]:
            secteur_par_uai[uai] = ps["clg_rne"]
base["secteur_id"] = base["uai"].map(secteur_par_uai)

secteur_features = []
for f in polys:
    p = f["properties"]
    geom = shape(f["geometry"]).simplify(SIMPLIFY_DEG, preserve_topology=True)
    g = mapping(geom)
    g["coordinates"] = json.loads(re.sub(r"(\d+\.\d{5})\d+", r"\1", json.dumps(g["coordinates"])))
    secteur_features.append(
        {
            "type": "Feature",
            "id": p["clg_rne"],
            "properties": {
                "secteur_id": p["clg_rne"],
                "secteur": p["clg_sec"],
                "commune": p["clg_ville"].title(),
                "code_insee": p["clg_insee"].strip() or None,
                "departement": p["clg_dep"].title(),
            },
            "geometry": g,
        }
    )
geojson = DATA / "colleges_secteurs.geojson"
geojson.write_text(
    json.dumps({"type": "FeatureCollection", "features": secteur_features}, ensure_ascii=False,
               separators=(",", ":"))
)  # fmt: skip

# --- 3. Effectifs par niveau (rentrées 2019-2025), dépt 45 ------------------------------------
eff = ods(EFFECTIFS, "code_dept='45'")
eff["rentree"] = pd.to_numeric(eff["rentree_scolaire"])
eff = eff.rename(columns={
    "numero_college": "uai", "nombre_eleves_total": "effectif_total",
    "nombre_total_de_6emes": "effectif_6e", "nombre_total_de_5emes": "effectif_5e",
    "nombre_total_de_4emes": "effectif_4e", "nombre_total_de_3emes": "effectif_3e",
    "nombre_d_eleves_total_segpa": "effectif_segpa", "nombre_d_eleves_total_ulis": "effectif_ulis",
    "rep": "rep", "rep0": "rep_plus",
})  # fmt: skip
eff = eff[["uai", "rentree", "effectif_total", "effectif_6e", "effectif_5e", "effectif_4e",
           "effectif_3e", "effectif_segpa", "effectif_ulis", "rep", "rep_plus"]]  # fmt: skip
# the ministry file also lists lycées professionnels, a collège closed in 2019...: the join on the
# 70 GéoLoiret UAI drops them.

# --- 4. IPS: trois jeux consécutifs (2016-2021, 2022, 2023-2025) ------------------------------
ips_parts = []
for ds in IPS:
    d = ods(ds, "code_du_departement='045' or code_du_departement='45'")  # 2 codages selon le jeu
    d["source_ips"] = ds
    ips_parts.append(d)
ips = pd.concat(ips_parts, ignore_index=True)
ips["rentree"] = ips["rentree_scolaire"].str[:4].astype(int)
ips = ips.rename(columns={"ecart_type_de_l_ips": "ips_ecart_type"})[
    ["uai", "rentree", "ips", "ips_ecart_type"]
]  # fmt: skip
assert not ips.duplicated(["uai", "rentree"]).any()

# --- 5. Brevet: DNB par établissement (sessions <= 2021) + IVAC (sessions >= 2022) ------------
# La session S du brevet clôt l'année scolaire S-1 / S: on la rattache à la rentrée S-1.
dnb_old = ods(DNB, "code_departement='045'")
dnb_old["taux"] = pd.to_numeric(
    dnb_old["taux_de_reussite"].str.replace("%", "").str.replace(",", "."), errors="coerce"
)  # fmt: skip
mentions = ["nombre_d_admis_mention_ab", "admis_mention_bien", "admis_mention_tres_bien"]
dnb_old["dnb_taux_mention"] = (dnb_old[mentions].sum(axis=1, min_count=3) / dnb_old["presents"]
                               * 100).round(1)  # fmt: skip
dnb_old = dnb_old.rename(columns={"numero_d_etablissement": "uai", "presents": "dnb_candidats",
                                  "taux": "dnb_taux_reussite"})  # fmt: skip
dnb_old["rentree"] = dnb_old["session"].astype(int) - 1
dnb_old["source_dnb"] = "dnb-par-etablissement"
dnb_new = ods(IVAC, "code_departement='45'")
dnb_new["rentree"] = dnb_new["session"].astype(int) - 1
dnb_new["dnb_taux_mention"] = (dnb_new["nb_mentions_global_g"] / dnb_new["nb_candidats_g"]
                               * 100).round(1)  # fmt: skip
dnb_new = dnb_new.rename(columns={
    "nb_candidats_g": "dnb_candidats", "taux_de_reussite_g": "dnb_taux_reussite",
    "va_du_taux_de_reussite_g": "dnb_valeur_ajoutee",
})  # fmt: skip
dnb_new["source_dnb"] = "ivac"
cols = ["uai", "rentree", "dnb_candidats", "dnb_taux_reussite", "dnb_taux_mention", "source_dnb"]
dnb = pd.concat([dnb_old[cols], dnb_new[cols + ["dnb_valeur_ajoutee"]]], ignore_index=True)
assert not dnb.duplicated(["uai", "rentree"]).any(), "plusieurs lignes DNB par UAI et session"

# --- 6. Jointure: 70 collèges x rentrées où au moins deux sources se recouvrent ---------------
rentrees = sorted(set(eff["rentree"]) | set(ips["rentree"]) | set(dnb["rentree"]))
src_years = {"effectifs": set(eff["rentree"]), "ips": set(ips["rentree"]),
             "dnb": set(dnb["rentree"])}  # fmt: skip
keep = [y for y in rentrees if sum(y in s for s in src_years.values()) >= 2]
grid = base.merge(pd.DataFrame({"rentree": keep}), how="cross")
df = (grid.merge(eff, on=["uai", "rentree"], how="left")
      .merge(ips, on=["uai", "rentree"], how="left")
      .merge(dnb, on=["uai", "rentree"], how="left"))  # fmt: skip
# Collèges ouverts après 2016 (Dadonville, Pithiviers): pas de ligne avant leur première année.
df = df.dropna(subset=["effectif_total", "ips", "dnb_taux_reussite"], how="all")
df["annee_scolaire"] = df["rentree"].astype(str) + "-" + (df["rentree"] + 1).astype(str)
df["session_dnb"] = df["rentree"] + 1
for c in ["rep", "rep_plus"]:
    df[c] = df[c].astype("Int64")
for c in [
    "effectif_total",
    "effectif_6e",
    "effectif_5e",
    "effectif_4e",
    "effectif_3e",
    "effectif_segpa",
    "effectif_ulis",
    "dnb_candidats",
]:
    df[c] = df[c].astype("Int64")  # fmt: skip
df = df[["uai", "nom", "commune", "code_insee", "statut", "lat", "lon", "secteur_id",
         "rentree", "annee_scolaire", "effectif_total", "effectif_6e", "effectif_5e",
         "effectif_4e", "effectif_3e", "effectif_segpa", "effectif_ulis", "rep", "rep_plus",
         "ips", "ips_ecart_type", "session_dnb", "dnb_candidats", "dnb_taux_reussite",
         "dnb_taux_mention", "dnb_valeur_ajoutee", "source_dnb"]]  # fmt: skip
df = df.sort_values(["uai", "rentree"]).reset_index(drop=True)
path = save_parquet(df, "colleges")

# --- Contrôles ---------------------------------------------------------------------------------
print("collèges:", len(base), base["statut"].value_counts().to_dict())
print("rentrées gardées:", keep, "| sources:", {k: (min(v), max(v)) for k, v in src_years.items()})
for name, s in [("effectifs", eff), ("ips", ips), ("dnb", dnb)]:
    n = s[s["uai"].isin(base["uai"])]["uai"].nunique()
    print(f"UAI des 70 collèges retrouvés dans {name}: {n}/70")
print(
    "secteur_id trouvé:",
    base["secteur_id"].notna().sum(),
    "/ 70 (public:",
    base.loc[base["statut"] == "public", "secteur_id"].notna().sum(),
    ")",
)
print(
    "secteurs sans collège dans les 70:",
    sorted(set(secteurs_raw["clg_rne"]) - set(base["secteur_id"].dropna())),
)
print("lignes:", df.shape, "| taille geojson (Mo):", round(geojson.stat().st_size / 1e6, 2))
print("valeurs manquantes par colonne:\n", df.isna().sum().to_string())

# --- Figure de départ: évolution des effectifs 2019 -> 2025, collèges publics -------------------
y0, y1 = int(eff["rentree"].min()), int(eff["rentree"].max())
pub = df[df["statut"] == "public"].pivot(index="nom", columns="rentree", values="effectif_total")
evo = (pub[y1] - pub[y0]).dropna().astype(int).sort_values()
gagnent, perdent = int((evo > 0).sum()), int((evo < 0).sum())
total0, total1 = int(pub.loc[evo.index, y0].sum()), int(pub.loc[evo.index, y1].sum())
title = (
    f"Entre {y0} et {y1}, {gagnent} collèges publics du Loiret ont gagné des élèves et "
    f"{perdent} en ont perdu ({fr(total0)} puis {fr(total1)} élèves au total, "
    f"n = {len(evo)} collèges publics présents aux deux rentrées)"
)
extremes = pd.concat([evo.head(10), evo.tail(10)])
fig = go.Figure(go.Bar(
    x=extremes.values, y=extremes.index, orientation="h",
    marker_color=[VERMILLION if v < 0 else BLUE for v in extremes.values],
    text=[f"{v:+d}" for v in extremes.values], textposition="outside",
))  # fmt: skip
fig.update_layout(
    xaxis_title=f"Variation des effectifs, rentrée {y0} à rentrée {y1} (élèves)",
    yaxis={"title": "", "tickfont": {"size": 12}, "automargin": True},
    font={"size": 14},
    showlegend=False,
)
fig.update_xaxes(range=[extremes.min() * 1.25, extremes.max() * 1.25])
save_figure(style(fig, title), "colleges")
print(title)

record(
    "colleges", df, path, None,
    f"{CATALOGUE} (collèges publics et privés: {COLLEGES_URL}; secteurs: {SECTEURS_URL}) ; "
    f"https://data.education.gouv.fr/explore/dataset/{EFFECTIFS}/ ; "
    + " ; ".join(f"https://data.education.gouv.fr/explore/dataset/{d}/" for d in IPS)
    + f" ; https://data.education.gouv.fr/explore/dataset/{DNB}/ ; "
    f"https://data.education.gouv.fr/explore/dataset/{IVAC}/",
    "Licence Ouverte v2.0 (Etalab) pour les jeux du ministère; GéoLoiret: licence indiquée sur "
    "les fiches du catalogue du Département",
    title,
    note=f"{len(base)} collèges ({(base['statut'] == 'public').sum()} publics) x "
    f"{len(keep)} rentrées; jointure sur le code UAI; geojson des secteurs: "
    f"colleges_secteurs.geojson ({len(secteur_features)} secteurs, clé secteur_id = UAI)",
    period_note=f"rentrées {min(keep)} à {max(keep)}: effectifs {y0}-{y1}, IPS "
    f"{ips['rentree'].min()}-{ips['rentree'].max()}, brevet sessions "
    f"{min(dnb_old['session'].astype(int))}-{dnb_new['session'].astype(int).max()} "
    "(DNB par établissement jusqu'en 2021, IVAC ensuite); on ne garde que les rentrées "
    "couvertes par au moins deux sources",
)  # fmt: skip
