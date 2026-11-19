"""Cas Risques naturels et technologiques dans le Loiret: une ligne par commune.

Sources (toutes en Licence Ouverte Etalab 2.0):
- GéoLoiret (Département du Loiret): aléa retrait-gonflement des argiles (BRGM), cavités
  souterraines (BRGM), mouvements de terrain (BRGM), périmètres des PPRI (DDT 45), repères de
  crues, ICPE (installations classées), réseau routier TMD, centrales nucléaires, collèges.
- Géorisques, base GASPAR: arrêtés de catastrophe naturelle (CatNat) par commune et DICRIM.
  Les données de l'API Géorisques (/api/v1/gaspar/catnat) sont celles de l'export GASPAR en
  fichiers (files.georisques.fr/GASPAR/gaspar.zip), que ce script lit: l'API a refusé les
  connexions pendant la préparation (connection reset), pas le fichier.
- Communes: contours de GéoLoiret (cache local) ou geo.api.gouv.fr. Population: cas territoire_loiret.

Sorties dans data/projets/: risques_communes.parquet, risques_catnat.parquet,
risques_communes.geojson (+ la figure de départ et la fiche dans summary.json).
"""

import io
import json
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import shapely
from common import DATA, download, fr, record, save_figure, save_parquet, style

GEOLOIRET = "https://geoloiret.loiret-numerique.fr/ags25/rest/services/"
ISOGEO = "https://open.isogeo.com/apiquery/hostedRessources/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/"
ZIPS = {
    "argiles": ISOGEO + "f6fcc6e9ffee4c58b291574a6225526e/8a927e45dba04b2fbb7a0bc1ffd9237d.bin/GEORISQUE_RETRAIT_GONFLEMENT_ARGILE.zip",
    "cavites": ISOGEO + "e51058e7f85440198ccb037487bc3338/c0eedfb2663746fd9bd42bf6ef0736be.bin/GEORISQUE_CAVITES_SOUTERRAINES.zip",
    "mouvements": ISOGEO + "6e3cbd9602b54de0a560a0236df55035/69a86b24f3b04e17a2704813c9310549.bin/GEORISQUE_MOUVEMENTS_TERRAIN.zip",
    "crues": ISOGEO + "f20adecdaadc4a0897c43d29a90fa29a/8713e72b09c54b6881a72059b7623519.bin/CD45_REPERES_CRUES.zip",
}  # fmt: skip
FEATURE_SERVERS = {
    "ppri": "III_12_Zones_a_risque_naturel/DDT_PERIMETRE_PPRIS_CD45/FeatureServer/46",
    "icpe": "III_8_Lieux_Production_Sites_Indus/NSTALLATION_INDUSTRIELLE_ICPE/FeatureServer/5",
    "tmd": "I_7_Reseaux_Transports/RESEAU_ROUTIER_TMD/FeatureServer/1",
    "nucleaire": "III_2_Batiment/CENTRALES_NUCLEAIRES/FeatureServer/0",
    "colleges": "III_2_Batiment/ETABLISSEMENTS_SCOLAIRES/FeatureServer/4",
}  # fmt: skip
GASPAR_ZIP = "https://files.georisques.fr/GASPAR/gaspar.zip"
L93 = 2154
PERIL = {
    "SEC": "Sécheresse",
    "ICB": "Inondations et/ou Coulées de Boue",
    "MVT": "Mouvement de terrain",
}


def feature_server(path):
    """All features of an ArcGIS FeatureServer layer, in WGS84, paginated."""
    features, offset = [], 0
    while True:
        raw = download(GEOLOIRET + path + "/query", where="1=1", outFields="*", outSR=4326,
                       f="geojson", resultOffset=offset, resultRecordCount=1000)  # fmt: skip
        page = json.loads(raw)["features"]
        features += page
        if len(page) < 1000:
            break
        offset += len(page)
    return gpd.GeoDataFrame.from_features(features, crs=4326)


def shapefile_zip(url):
    """Download a zipped shapefile (Lambert-93) and read it."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "layer.zip"
        path.write_bytes(download(url))
        return gpd.read_file(f"zip://{path}")


def share_of(communes, layer):
    """Share (%) of each commune's area covered by the layer (polygons in Lambert-93)."""
    inter = gpd.overlay(communes[["code_insee", "geometry"]], layer, how="intersection")
    area = inter.geometry.area.groupby(inter["code_insee"]).sum()
    full = communes.set_index("code_insee").geometry.area
    return (100 * area.reindex(full.index).fillna(0) / full).clip(upper=100)


# ---------------------------------------------------------------- communes + population
cache = Path(__file__).resolve().parent / "data" / "cache" / "geoloiret" / "communes.geojson"  # écrit par old_data.py
if cache.exists():
    communes = gpd.read_file(cache).rename(columns={"insee_com": "code_insee", "nom": "commune"})
else:
    geo = download("https://geo.api.gouv.fr/departements/45/communes",
                   fields="code,nom,contour", format="geojson", geometry="contour")  # fmt: skip
    communes = gpd.GeoDataFrame.from_features(json.loads(geo)["features"], crs=4326)
    communes = communes.rename(columns={"code": "code_insee", "nom": "commune"})
communes = communes[["code_insee", "commune", "geometry"]].to_crs(L93)
communes["geometry"] = shapely.make_valid(communes.geometry.values)
assert communes["code_insee"].is_unique and len(communes) == 325, len(communes)
communes["superficie_km2"] = (communes.geometry.area / 1e6).round(2)
centre = communes.geometry.centroid.to_crs(4326)
communes["lat"], communes["lon"] = centre.y.round(5), centre.x.round(5)

pop = pd.read_parquet(DATA / "territoire_loiret.parquet", columns=["code_insee", "population_2023"])
communes = communes.merge(pop, on="code_insee", how="left")
print("communes sans population:", communes["population_2023"].isna().sum())

# ---------------------------------------------------------------- aléa argiles (RGA)
argiles = shapefile_zip(ZIPS["argiles"])
print(f"argiles: {len(argiles)} entités, {argiles.geometry.isna().sum()} sans géométrie")
argiles = argiles[argiles.geometry.notna()].copy()
argiles["geometry"] = shapely.make_valid(argiles.geometry.values)
niveaux = {
    n: argiles[argiles["alea"] == n].geometry.union_all() for n in ("Fort", "Moyen", "Faible")
}
# Exclusive classes (the highest hazard wins where polygons overlap)
fort = niveaux["Fort"]
moyen = niveaux["Moyen"].difference(fort)
faible = niveaux["Faible"].difference(fort).difference(moyen)
for nom, geom in (("fort", fort), ("moyen", moyen), ("faible", faible)):
    layer = gpd.GeoDataFrame(geometry=[geom], crs=L93)
    communes[f"pct_argiles_{nom}"] = share_of(communes, layer).round(1).to_numpy()

# ---------------------------------------------------------------- cavités et mouvements de terrain
cavites = shapefile_zip(ZIPS["cavites"])
print(f"cavités: {len(cavites)} entités, {cavites.geometry.isna().sum()} sans géométrie")
cavites = cavites[cavites.geometry.notna()]
# 48 points sit outside the département (wrong coordinates in the source): one is 13 m from a
# commune edge and is kept (nearest commune within 200 m), the other 47 are left out.
joined = gpd.sjoin_nearest(cavites[["geometry"]], communes[["code_insee", "geometry"]],
                           max_distance=200)  # fmt: skip
joined = joined[~joined.index.duplicated()]
print(f"cavités rattachées à une commune: {len(joined)} sur {len(cavites)} localisées")
communes["nb_cavites"] = (
    communes["code_insee"].map(joined.groupby("code_insee").size()).fillna(0).astype(int)
)

# Mouvements: the commune code of the source; where that code is not one of the 325 current
# communes (14 points, 2 codes), the commune that contains the point.
mouvements = shapefile_zip(ZIPS["mouvements"])
mouvements["code_insee"] = mouvements["code_insee"].astype("Int64").astype(str).str.zfill(5)
inconnu = ~mouvements["code_insee"].isin(communes["code_insee"])
print(f"mouvements: {len(mouvements)} entités, code commune inconnu: {inconnu.sum()}")
fix = gpd.sjoin(mouvements[inconnu][["geometry"]], communes[["code_insee", "geometry"]],
                predicate="within")  # fmt: skip
mouvements.loc[fix.index, "code_insee"] = fix["code_insee"]
assert mouvements["code_insee"].isin(communes["code_insee"]).all()
communes["nb_mouvements_terrain"] = communes["code_insee"].map(
    mouvements.groupby("code_insee").size()).fillna(0).astype(int)  # fmt: skip
communes["nb_effondrements"] = communes["code_insee"].map(
    mouvements[mouvements["type_mvt"] == "Effondrement"].groupby("code_insee").size()
).fillna(0).astype(int)  # fmt: skip

# ---------------------------------------------------------------- PPRI (périmètres) et repères de crues
ppri = feature_server(FEATURE_SERVERS["ppri"]).to_crs(L93)
ppri["geometry"] = shapely.make_valid(ppri.geometry.values)
communes["pct_ppri"] = share_of(communes, ppri[["geometry"]].dissolve()).round(1).to_numpy()
noms = {}
for _, p in ppri.iterrows():
    part = share_of(communes, gpd.GeoDataFrame(geometry=[p.geometry], crs=L93))
    for code in part[part >= 1].index:  # ignore slivers under 1 % of the commune
        noms.setdefault(code, []).append(p["libelle"])
communes["ppri"] = communes["code_insee"].map(lambda c: " ; ".join(sorted(noms.get(c, []))))
communes["nb_ppri"] = communes["code_insee"].map(lambda c: len(noms.get(c, [])))

crues = shapefile_zip(ZIPS["crues"])
crues["code_insee"] = crues["code_insee"].astype("Int64").astype(str).str.zfill(5)
communes["nb_reperes_crues"] = (
    communes["code_insee"].map(crues.groupby("code_insee").size()).fillna(0).astype(int)
)

# ---------------------------------------------------------------- ICPE (installations classées)
icpe = feature_server(FEATURE_SERVERS["icpe"])
print(icpe.groupby(["seveso", "lib_seveso"]).size().to_string())
seveso = icpe["lib_seveso"].str.startswith("Seveso")
par_commune = {
    "nb_icpe": icpe.groupby("cd_insee").size(),
    "nb_icpe_autorisation": icpe[icpe["lib_regime"] == "Autorisation"].groupby("cd_insee").size(),
    "nb_seveso": icpe[seveso].groupby("cd_insee").size(),
    "nb_seveso_seuil_haut": icpe[icpe["lib_seveso"] == "Seveso seuil haut"].groupby("cd_insee").size(),
}  # fmt: skip
for col, serie in par_commune.items():
    communes[col] = communes["code_insee"].map(serie).fillna(0).astype(int)
print(
    "ICPE dont la commune n'est pas dans le Loiret:",
    (~icpe["cd_insee"].isin(communes["code_insee"])).sum(),
)

# ---------------------------------------------------------------- transport de matières dangereuses
tmd = feature_server(FEATURE_SERVERS["tmd"]).to_crs(L93)
print(tmd["type"].map(repr).value_counts().to_string())
# lines first: the overlay keeps the geometry type of its first layer
cut = gpd.overlay(tmd[["type", "geometry"]], communes[["code_insee", "geometry"]],
                  how="intersection", keep_geom_type=True)  # fmt: skip
km = (
    (cut.geometry.length / 1000)
    .groupby([cut["code_insee"], cut["type"]])
    .sum()
    .unstack(fill_value=0)
)
print(
    km.sum().round(1).to_dict(),
    "km; tronçons TMD longueur totale:",
    round(tmd.length.sum() / 1000, 1),
)
for col, kind in (("km_tmd_autoroutes", "Autoroute"), ("km_tmd_routes_dep", "Routes"),
                  ("km_tmd_voies_ferrees", "Voies ferrées")):  # fmt: skip
    communes[col] = communes["code_insee"].map(km[kind]).fillna(0).round(2)

# ---------------------------------------------------------------- centrales nucléaires, collèges
nuc = feature_server(FEATURE_SERVERS["nucleaire"]).to_crs(L93)
pts = communes.geometry.centroid
dist = np.array([[p.distance(c) / 1000 for c in nuc.geometry] for p in pts])
communes["distance_centrale_km"] = dist.min(axis=1).round(1)
communes["centrale_proche"] = nuc["nom"].to_numpy()[dist.argmin(axis=1)]

colleges = feature_server(FEATURE_SERVERS["colleges"]).to_crs(L93)
col = gpd.sjoin(colleges[["geometry"]], communes[["code_insee", "geometry"]], predicate="within")
communes["nb_colleges"] = (
    communes["code_insee"].map(col.groupby("code_insee").size()).fillna(0).astype(int)
)
dans_ppri = col[col.geometry.within(ppri.union_all())]
communes["nb_colleges_dans_ppri"] = communes["code_insee"].map(
    dans_ppri.groupby("code_insee").size()).fillna(0).astype(int)  # fmt: skip
print(
    f"collèges: {len(colleges)}, hors communes: {len(colleges) - len(col)}, "
    f"dans un périmètre PPRI: {len(dans_ppri)}"
)

# ---------------------------------------------------------------- GASPAR: CatNat et DICRIM
with zipfile.ZipFile(io.BytesIO(download(GASPAR_ZIP))) as z:
    names = {n.split("_gaspar")[0]: n for n in z.namelist()}
    raw = pd.read_csv(z.open(names["catnat"]), sep=";", dtype=str)
    dicrim = pd.read_csv(z.open(names["dicrim"]), sep=";", dtype=str)
print("export GASPAR:", names["catnat"])
raw = raw[raw["code_commune"].isin(communes["code_insee"])].copy()
for col in ("date_debut", "date_fin", "date_signature_arrete", "date_publication_jo"):
    raw[col] = pd.to_datetime(raw[col], errors="coerce").dt.normalize()
dup = raw.duplicated(["id_gaspar", "code_commune", "num_risque_jo"], keep="first")
print("lignes CatNat en double (même arrêté, commune, péril) retirées:", dup.sum())
raw = raw[~dup]
catnat = pd.DataFrame({
    "code_insee": raw["code_commune"],
    "commune": raw["code_commune"].map(communes.set_index("code_insee")["commune"]),
    "id_arrete": raw["id_gaspar"],
    "code_peril": raw["num_risque_jo"],
    "peril": raw["lib_risque_jo"],
    "date_debut": raw["date_debut"],
    "date_fin": raw["date_fin"],
    "date_arrete": raw["date_signature_arrete"],
    "date_jo": raw["date_publication_jo"],
})  # fmt: skip
catnat = catnat.sort_values(["date_debut", "code_insee", "code_peril"]).reset_index(drop=True)

communes["nb_catnat"] = (
    communes["code_insee"]
    .map(catnat.groupby("code_insee")["id_arrete"].nunique())
    .fillna(0)
    .astype(int)
)
for code, col in (("SEC", "secheresse"), ("ICB", "inondations"), ("MVT", "mouvement_terrain")):
    n = catnat[catnat["code_peril"] == code].groupby("code_insee").size()
    communes[f"nb_catnat_{col}"] = communes["code_insee"].map(n).fillna(0).astype(int)
autres = catnat[~catnat["code_peril"].isin(list(PERIL))]
communes["nb_catnat_autres"] = (
    communes["code_insee"].map(autres.groupby("code_insee").size()).fillna(0).astype(int)
)
communes["annee_dernier_catnat"] = communes["code_insee"].map(
    catnat.groupby("code_insee")["date_debut"].max().dt.year
)

dicrim = dicrim[dicrim["cod_commune"].isin(communes["code_insee"])]
communes["annee_dicrim"] = communes["code_insee"].map(
    dicrim.assign(a=pd.to_datetime(dicrim["dat_publi_dicrim"]).dt.year).groupby("cod_commune")["a"].min()
)  # fmt: skip

# ---------------------------------------------------------------- outputs
cols = [
    "code_insee", "commune", "population_2023", "superficie_km2",
    "pct_argiles_fort", "pct_argiles_moyen", "pct_argiles_faible",
    "nb_cavites", "nb_mouvements_terrain", "nb_effondrements",
    "pct_ppri", "ppri", "nb_ppri", "nb_reperes_crues",
    "nb_icpe", "nb_icpe_autorisation", "nb_seveso", "nb_seveso_seuil_haut", "km_tmd_autoroutes", "km_tmd_routes_dep", "km_tmd_voies_ferrees",
    "distance_centrale_km", "centrale_proche", "nb_colleges", "nb_colleges_dans_ppri",
    "nb_catnat", "nb_catnat_secheresse", "nb_catnat_inondations", "nb_catnat_mouvement_terrain",
    "nb_catnat_autres", "annee_dernier_catnat", "annee_dicrim", "lat", "lon",
]  # fmt: skip
df = (
    pd.DataFrame(communes[cols])
    .sort_values("population_2023", ascending=False)
    .reset_index(drop=True)
)
df["annee_dernier_catnat"] = df["annee_dernier_catnat"].astype("Int64")
df["annee_dicrim"] = df["annee_dicrim"].astype("Int64")
path = save_parquet(df, "risques_communes")
path_catnat = save_parquet(catnat, "risques_catnat")

# GeoJSON for choropleths: simplified in Lambert-93 (30 m), then WGS84 with 5 decimals
simple = communes[["code_insee", "commune", "geometry"]].copy()
simple["geometry"] = simple.geometry.simplify(30, preserve_topology=True)
simple = simple.to_crs(4326)
simple["geometry"] = shapely.set_precision(simple.geometry.values, 1e-5)
features = [
    {"type": "Feature", "id": r.code_insee,
     "properties": {"code_insee": r.code_insee, "commune": r.commune},
     "geometry": json.loads(shapely.to_geojson(r.geometry))}
    for r in simple.itertuples()
]  # fmt: skip
geojson_path = DATA / "risques_communes.geojson"
geojson_path.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                                   ensure_ascii=False, separators=(",", ":")))  # fmt: skip
print(f"geojson: {geojson_path.stat().st_size / 1e6:.2f} Mo")

# ---------------------------------------------------------------- figure de départ
annee = catnat["date_debut"].dt.year
total = len(catnat)
sec = int((catnat["code_peril"] == "SEC").sum())
title = (
    f"La sécheresse motive {sec} des {fr(total)} reconnaissances de catastrophe naturelle des "
    f"communes du Loiret, dont {int((annee[catnat['code_peril'] == 'SEC'] >= 2016).sum())} depuis 2016 "
    f"(n = {fr(total)} décisions pour {len(df)} communes, {annee.min()}-{annee.max()})"
)
par_an = (catnat.assign(annee=annee, peril=catnat["peril"].where(catnat["code_peril"].isin(PERIL),
                                                                  "Autres périls"))
          .groupby(["annee", "peril"]).size().reset_index(name="decisions"))  # fmt: skip
fig = px.bar(par_an, x="annee", y="decisions", color="peril",
             labels={"annee": "Année du début de l'événement", "decisions": "Décisions",
                     "peril": ""},
             color_discrete_map={"Sécheresse": "#D55E00", "Inondations et/ou Coulées de Boue": "#0072B2",
                                 "Mouvement de Terrain": "#009E73", "Autres périls": "#999999"})  # fmt: skip
fig.update_layout(legend={"orientation": "h", "y": -0.25})
save_figure(style(fig, title), "risques")

sources = (
    "GéoLoiret (https://geoloiret.loiret-numerique.fr, catalogue https://open.isogeo.com/s/"
    "1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0): argiles RGA, cavités, "
    "mouvements de terrain (BRGM), PPRI (DDT 45), repères de crues, ICPE, TMD, centrales, collèges; "
    "Géorisques GASPAR (https://www.data.gouv.fr/datasets/base-nationale-de-gestion-assistee-des-procedures-administratives-relatives-aux-risques-gaspar, "
    "export " + GASPAR_ZIP + ", API https://www.georisques.gouv.fr/doc-api); "
    "population: cas territoire_loiret (INSEE)"
)
record(
    "risques",
    df,
    path,
    None,
    sources,
    "Licence Ouverte v2.0 (Etalab), vérifiée sur les fiches GéoLoiret (mention: Source: BRGM / DDT45 / "
    "Département du Loiret - année) et sur la fiche data.gouv.fr de GASPAR (licence ouverte)",
    title,
    note=f"{len(df)} communes; {len(catnat)} décisions CatNat ({catnat['id_arrete'].nunique()} arrêtés) "
    f"du {catnat['date_debut'].min():%Y-%m-%d} au {catnat['date_debut'].max():%Y-%m-%d}; "
    f"{int(df['nb_cavites'].sum())} cavités, {int(df['nb_mouvements_terrain'].sum())} mouvements de terrain, "
    f"{int(df['nb_icpe'].sum())} ICPE; fichiers liés: risques_catnat.parquet (format long, 1 ligne par "
    "arrêté × commune × péril) et risques_communes.geojson (contours simplifiés, clé id = code INSEE)",
    period_note="CatNat: événements de "
    f"{catnat['date_debut'].min():%Y} à {catnat['date_debut'].max():%Y} (export GASPAR du 2026-11-02); "
    "couches GéoLoiret mises à jour de 2024 à 2026 selon la fiche",
)
print(df.shape, catnat.shape)
print(title)
print(df.isna().sum()[lambda s: s > 0].to_dict())
