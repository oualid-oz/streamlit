"""Cas Collèges et risques: une ligne par collège du Loiret, exposée aux risques autour de son point.

Croise les 70 collèges (colleges.parquet, rentrée 2025) avec les couches de risques de GéoLoiret
(mêmes sources que build_risques.py: argiles RGA, PPRI, cavités, mouvements de terrain, ICPE,
TMD, centrales nucléaires, repères de crues) et avec le contexte communal de
risques_communes.parquet (arrêtés CatNat, DICRIM). Les distances sont calculées en Lambert-93.
"""

import json
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from common import DATA, download, record, save_parquet

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
    "tmd_zone": "I_7_Reseaux_Transports/RESEAU_ROUTIER_TMD/FeatureServer/2",
    "nucleaire": "III_2_Batiment/CENTRALES_NUCLEAIRES/FeatureServer/0",
}  # fmt: skip
L93 = 2154
RENTREE = 2025
# Radii and thresholds (all distances in Lambert-93 metres)
RAYON_CAVITES_M = 500  # cavités comptées autour du collège
RAYON_MOUVEMENTS_M = 500  # mouvements de terrain comptés autour du collège
RAYON_ICPE_M = 1000  # installations classées comptées autour du collège
ZONE_TMD_M = 500  # zone de sûreté TMD (largeur de la couche GéoLoiret)


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


def nearest(points, layer, **kw):
    """Distance (m) from each point to the nearest feature of `layer`, plus that feature's row."""
    joined = gpd.sjoin_nearest(points[["geometry"]], layer, distance_col="distance_m", **kw)
    return joined[~joined.index.duplicated()].reindex(points.index)


def count_within(points, layer, radius_m):
    """Number of features of `layer` within radius_m of each point."""
    pairs = gpd.sjoin(points[["geometry"]].assign(geometry=points.buffer(radius_m)),
                      layer[["geometry"]], predicate="intersects")  # fmt: skip
    return pairs.groupby(level=0).size().reindex(points.index).fillna(0).astype(int)


# ---------------------------------------------------------------- collèges (rentrée 2025)
base = pd.read_parquet(DATA / "colleges.parquet")
base = base[base["rentree"] == RENTREE]
cols = ["uai", "nom", "commune", "code_insee", "statut", "lat", "lon", "secteur_id",
        "effectif_total", "ips"]  # fmt: skip
df = base[cols].reset_index(drop=True)
assert len(df) == 70 and df["uai"].is_unique, len(df)
pts = gpd.GeoDataFrame(df[["uai"]], geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs=4326)
pts = pts.to_crs(L93)

# ---------------------------------------------------------------- argiles: class at the point
argiles = shapefile_zip(ZIPS["argiles"])
argiles = argiles[argiles.geometry.notna()].copy()
argiles["geometry"] = shapely.make_valid(argiles.geometry.values)
classe = pd.Series("non cartographié", index=pts.index)
for niveau in ("Faible", "Moyen", "Fort"):  # the highest hazard is applied last, so it wins
    zone = argiles[argiles["alea"] == niveau][["geometry"]]
    dedans = gpd.sjoin(pts[["geometry"]], zone, predicate="within").index.unique()
    classe.loc[dedans] = niveau.lower()
df["argiles_classe"] = classe.to_numpy()

# ---------------------------------------------------------------- PPRI: inside a perimeter
ppri = feature_server(FEATURE_SERVERS["ppri"]).to_crs(L93)
ppri["geometry"] = shapely.make_valid(ppri.geometry.values)
dans = gpd.sjoin(pts[["geometry"]], ppri[["libelle", "geometry"]], predicate="within")
noms = dans.groupby(level=0)["libelle"].agg(lambda s: " ; ".join(sorted(s)))
df["dans_ppri"] = pts.index.isin(dans.index)
df["ppri"] = noms.reindex(pts.index).fillna("").to_numpy()

# ---------------------------------------------------------------- cavités et mouvements de terrain
cavites = shapefile_zip(ZIPS["cavites"])
cavites = cavites[cavites.geometry.notna()]
df["nb_cavites_500m"] = count_within(pts, cavites, RAYON_CAVITES_M).to_numpy()
mouvements = shapefile_zip(ZIPS["mouvements"])
df["nb_mouvements_terrain_500m"] = count_within(pts, mouvements, RAYON_MOUVEMENTS_M).to_numpy()

# ---------------------------------------------------------------- ICPE and Seveso
icpe = feature_server(FEATURE_SERVERS["icpe"]).to_crs(L93)
df["distance_icpe_km"] = (nearest(pts, icpe)["distance_m"] / 1000).round(2).to_numpy()
seveso = icpe[icpe["lib_seveso"].str.startswith("Seveso")]
df["distance_seveso_km"] = (nearest(pts, seveso)["distance_m"] / 1000).round(2).to_numpy()
df["nb_icpe_1km"] = count_within(pts, icpe, RAYON_ICPE_M).to_numpy()

# ---------------------------------------------------------------- TMD: nearest axis and 500 m safety zone
tmd = feature_server(FEATURE_SERVERS["tmd"]).to_crs(L93)
near = nearest(pts, tmd[["type", "geometry"]])
df["distance_tmd_m"] = near["distance_m"].round(0).astype(int).to_numpy()
df["type_tmd_proche"] = near["type"].to_numpy()
zone = feature_server(FEATURE_SERVERS["tmd_zone"]).to_crs(L93)
zone["geometry"] = shapely.make_valid(zone.geometry.values)
df["dans_zone_tmd_500m"] = pts.index.isin(gpd.sjoin(pts[["geometry"]], zone[["geometry"]],
                                                    predicate="within").index)  # fmt: skip

# ---------------------------------------------------------------- nuclear plants, flood marks
nuc = feature_server(FEATURE_SERVERS["nucleaire"]).to_crs(L93)
near = nearest(pts, nuc[["nom", "geometry"]])
df["distance_centrale_km"] = (near["distance_m"] / 1000).round(1).to_numpy()
df["centrale_proche"] = near["nom"].to_numpy()
crues = shapefile_zip(ZIPS["crues"])
crues = crues[crues.geometry.notna()]
df["distance_repere_crue_km"] = (nearest(pts, crues)["distance_m"] / 1000).round(2).to_numpy()

# ---------------------------------------------------------------- commune context
contexte = pd.read_parquet(
    DATA / "risques_communes.parquet",
    columns=["code_insee", "nb_catnat", "nb_catnat_inondations", "nb_catnat_secheresse",
             "nb_catnat_mouvement_terrain", "annee_dicrim"],
)  # fmt: skip
df = df.merge(contexte, on="code_insee", how="left", validate="m:1")
assert len(df) == 70

df["effectif_total"] = df["effectif_total"].astype("Int64")
path = save_parquet(df, "colleges_risques")

public = df[df["statut"] == "public"]
note = (
    f"{len(df)} collèges ({len(public)} publics, {len(df) - len(public)} privés), rentrée {RENTREE} "
    f"({int(df['effectif_total'].sum())} élèves); exposition mesurée au point du collège: "
    f"argiles au point, PPRI au point, cavités et mouvements dans {RAYON_CAVITES_M} m, ICPE dans "
    f"{RAYON_ICPE_M} m, zone TMD {ZONE_TMD_M} m; distances en Lambert-93; contexte communal depuis "
    "risques_communes.parquet"
)
sources = (
    "colleges.parquet (cas Collèges); GéoLoiret (https://geoloiret.loiret-numerique.fr, catalogue "
    "https://open.isogeo.com/s/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0): "
    "argiles RGA, cavités, mouvements de terrain (BRGM), PPRI (DDT 45), ICPE, TMD, centrales, "
    "repères de crues; Géorisques GASPAR via risques_communes.parquet"
)
record(
    "colleges_risques", df, path, None, sources,
    "Licence Ouverte v2.0 (Etalab), vérifiée sur les fiches GéoLoiret (voir la fiche risques)",
    "", note=note,
    period_note=f"rentrée {RENTREE}; CatNat 1983-2025; couches GéoLoiret 2024-2026",
)  # fmt: skip
print(df.shape)
print(df.isna().sum()[lambda s: s > 0].to_dict())
