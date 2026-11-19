"""Cas OLD et véloroutes du Loiret: une ligne par tronçon de véloroute × commune.

Croise quatre sources (toutes mesurées en Lambert-93, EPSG:2154, en mètres) :
- le zonage d'influence des obligations légales de débroussaillement (OLD), fichier shapefile
  de l'État téléchargé sur GéoLoiret (data/old/, pas de service en ligne)
- les tracés des véloroutes du Département du Loiret (GéoLoiret, FeatureServer)
- les bois et forêts classés à risque d'incendie (GéoLoiret, FeatureServer)
- la BD TOPO de l'IGN (zones de végétation, surfaces en eau), via la Géoplateforme

La logique géométrique est celle de demos/old_data.py (la démo Streamlit app_old.py), importée
telle quelle. Lancer depuis demos/ : uv run --with geopandas python projets/build_old_veloroutes.py
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
from common import DATA, GREEN, ORANGE, VERMILLION, fr, record, save_figure, save_parquet, style

sys.path.insert(0, str(Path(__file__).resolve().parent))  # old_data.py, à côté
import old_data as od

# ---- Hypothèses (pas des règles de droit, sauf mention) -------------------------------------
# Largeur de la bande à débroussailler de chaque côté de la voie, mesurée depuis le bord de la
# voie. HYPOTHÈSE de travail : le code forestier (art. L134-10) fixe un plafond de 20 m de part
# et d'autre de l'emprise des voies ouvertes à la circulation publique, la largeur réelle est
# fixée par l'autorité administrative de l'État (le préfet). 10 m est un choix de la démo.
BANDE_M = 10
# Distance à la forêt fermée de l'IGN en dessous de laquelle un tronçon est dit « le long » d'un
# bois. HYPOTHÈSE : même valeur que la bande.
DISTANCE_FORET_M = 10
# Largeur de la voie elle-même (emprise), par type de voie : od.EMPRISES. HYPOTHÈSE : la couche
# des véloroutes ne donne aucune largeur (3 m pour une voie verte, 6 m pour une route...).
EMPRISES = od.EMPRISES
# Niveau d'intervention par nature de végétation BD TOPO : od.NATURES. HYPOTHÈSE de la démo.
NATURES = od.NATURES
# Simplification des géométries pour les GeoJSON, en mètres (Lambert-93), puis arrondi à 5
# décimales (≈ 1 m).
TOL_TRONCONS_M, TOL_ZONE_M, TOL_COMMUNES_M = 5, 30, 40

FICHES = (
    "https://open.isogeo.com/s/1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/r/"
)
SOURCES = {
    "zonage_old": FICHES + "30f4e50565cd46b894a2a37c7973f3fa",
    "veloroutes": FICHES + "194fd0fef6ac4f23abec83e726fee9d1",
    "veloroutes_service": od.ARCGIS + od.COUCHES["veloroutes"],
    "bois_classes": FICHES + "f50797014a9d427db5a33c3eaa239e84",
    "bois_classes_service": od.ARCGIS + od.COUCHES["bois"],
    "communes_service": od.ARCGIS + od.COUCHES["communes"],
    "bd_topo": "https://cartes.gouv.fr/rechercher-une-donnee/dataset/IGNF_BD-TOPO",
}
LICENCE = (
    "Zonage OLD, bois classés: Licence Ouverte Etalab 2.0 (fiches GéoLoiret, mention « Source : "
    "DDT »). Véloroutes: la fiche GéoLoiret ne nomme pas de licence, elle dit « usage libre sous "
    "réserve de mentionner Source : Département du Loiret - année ». Communes (BD TOPO sur "
    "GéoLoiret) et végétation (BD TOPO IGN, Géoplateforme): Licence Ouverte 2.0 selon la politique "
    "open data de l'IGN, à revérifier sur la page produit."
)


def troncons_par_commune() -> gpd.GeoDataFrame:
    """Chaque tronçon coupé aux limites des communes (un tronçon peut en traverser plusieurs)."""
    velo, communes = od.load_veloroutes(), od.load_communes()
    morceaux = gpd.overlay(
        velo,
        communes[["commune", "insee_com", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    ).rename(columns={"insee_com": "code_insee"})
    morceaux = morceaux[morceaux.length > 0].reset_index(drop=True)
    # Les bouts de tronçon hors des communes du Loiret (frontière) : une ligne « hors Loiret ».
    reste = velo.set_index("troncon").geometry.length - morceaux.groupby("troncon").apply(
        lambda d: d.length.sum(), include_groups=False
    ).reindex(velo["troncon"]).fillna(0).set_axis(velo["troncon"])
    hors = velo[velo["troncon"].isin(reste[reste > 1].index)]
    if len(hors):
        coupe = velo.set_index("troncon").geometry.difference(communes.union_all())
        hors = hors.assign(geometry=hors["troncon"].map(coupe).values)
        hors = hors[~hors.is_empty].assign(commune="hors Loiret", code_insee=pd.NA)
        morceaux = pd.concat([morceaux, hors], ignore_index=True)
    morceaux["id_ligne"] = (
        morceaux["troncon"].astype(str) + "-" + morceaux["code_insee"].fillna("HL")
    )
    return morceaux


def construire() -> tuple[pd.DataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    old = od.load_old()
    zone = old.union_all()
    m = troncons_par_commune()
    m["longueur_m"] = m.length
    m["_dedans"] = m.intersection(zone)
    m["longueur_dans_old_m"] = m["_dedans"].length

    bois = od.load_bois().union_all()  # fondu : les bois se recouvrent parfois
    m["longueur_bois_classe_m"] = m.intersection(bois).length.clip(upper=m["longueur_m"])

    # Tout ce qui suit ne concerne que la partie dans la zone OLD (la végétation IGN n'est
    # téléchargée que dans les 40 m autour des tronçons de la zone).
    dedans = m[m["longueur_dans_old_m"] > 0].copy()
    dedans["geometry"] = dedans["_dedans"]
    dedans = dedans[~dedans.is_empty]
    couvert = od.load_couvert(dedans)
    eau = od.load_couvert(dedans, "surface_hydrographique")
    fermee = couvert[couvert["nature"].str.startswith("Forêt fermée")].buffer(DISTANCE_FORET_M)
    pres_foret = dedans.intersection(fermee.union_all()).length

    demi = dedans["voie"].map(EMPRISES).fillna(EMPRISES[od.INCONNU]).astype(float) / 2
    # approche naïve : bande mesurée depuis le bord de la voie, sans rien retirer (voies, eau)
    brute = dedans.buffer(demi + BANDE_M).intersection(zone)
    bandes = od.bandes(dedans, zone, BANDE_M, EMPRISES, eau)
    # Aux jonctions, les bandes de deux tronçons voisins se recouvrent : on garde chaque mètre carré
    # une seule fois, pour le premier tronçon dans l'ordre de la table. La somme des lignes
    # est alors la vraie surface.
    deja, sans_doublon = None, []
    for forme in bandes.geometry:
        sans_doublon.append(forme if deja is None else forme.difference(deja))
        deja = forme if deja is None else deja.union(forme)
    bandes["geometry"] = sans_doublon
    pieces = od.par_intensite(bandes, couvert, NATURES)
    ha = od.hectares(pieces, "morceau").reindex(dedans.index).fillna(0)

    m["part_dans_old"] = (m["longueur_dans_old_m"] / m["longueur_m"]).clip(upper=1)
    m["part_bois_classe"] = (m["longueur_bois_classe_m"] / m["longueur_m"]).clip(upper=1)
    m.loc[dedans.index, "part_foret_fermee_ign"] = (
        pres_foret / dedans["longueur_dans_old_m"]
    ).clip(upper=1)
    m["emprise_voie_hyp_m"] = m["voie"].map(EMPRISES).fillna(EMPRISES[od.INCONNU])
    m["bande_hyp_m"] = BANDE_M
    m["ha_bande_brute"] = brute.area.div(10_000).reindex(m.index).fillna(0)
    m["ha_a_traiter"] = ha["ha"].reindex(m.index).fillna(0)
    for niveau, nom in zip(od.INTENSITES, ["forte", "moyenne", "legere", "courante"]):
        m[f"ha_{nom}"] = ha[niveau].reindex(m.index).fillna(0)
    milieux = gpd.GeoSeries(m.interpolate(0.5, normalized=True), crs=od.L93).to_crs(4326)
    m["lat"], m["lon"] = milieux.y.round(5), milieux.x.round(5)

    colonnes = [
        "id_ligne", "troncon", "itineraire", "gestionnaire", "voie", "revetement", "ouvert",
        "commune", "code_insee", "longueur_m", "longueur_dans_old_m", "part_dans_old",
        "longueur_bois_classe_m", "part_bois_classe", "part_foret_fermee_ign",
        "emprise_voie_hyp_m", "bande_hyp_m", "ha_bande_brute", "ha_a_traiter",
        "ha_forte", "ha_moyenne", "ha_legere", "ha_courante", "lat", "lon",
    ]  # fmt: skip
    df = pd.DataFrame(m[colonnes])
    arrondis = {"longueur_m": 0, "longueur_dans_old_m": 0, "longueur_bois_classe_m": 0,
                "part_dans_old": 3, "part_bois_classe": 3, "part_foret_fermee_ign": 3,
                "ha_bande_brute": 3, "ha_a_traiter": 3, "ha_forte": 3, "ha_moyenne": 3,
                "ha_legere": 3, "ha_courante": 3}  # fmt: skip
    df = df.round(arrondis)
    df["code_insee"] = df["code_insee"].astype("string")
    df = df.sort_values(["ha_forte", "ha_a_traiter"], ascending=False).reset_index(drop=True)
    return df, m, old


def arrondi(coords, n=5):
    if isinstance(coords[0], (int, float)):
        return [round(c, n) for c in coords]
    return [arrondi(c, n) for c in coords]


def ecrire_geojson(gdf, nom, id_col, tolerance_m, props) -> Path:
    """GeoJSON WGS 84 : un « id » par entité, coordonnées arrondies, géométries simplifiées."""
    g = gdf.copy()
    g["geometry"] = g.simplify(tolerance_m)
    g = g[~g.is_empty].to_crs(4326)
    feats = []
    for _, r in g.iterrows():
        geo = r.geometry.__geo_interface__
        feats.append({
            "type": "Feature",
            "id": str(r[id_col]),
            "properties": {p: (None if pd.isna(r[p]) else r[p]) for p in props},
            "geometry": {"type": geo["type"], "coordinates": arrondi(geo["coordinates"])},
        })  # fmt: skip
    chemin = DATA / f"{nom}.geojson"
    chemin.write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False,
                   separators=(",", ":"), default=lambda o: o.item() if hasattr(o, "item") else str(o))
    )  # fmt: skip
    return chemin


if __name__ == "__main__":
    df, m, old = construire()
    path = save_parquet(df, "old_veloroutes")

    # ---- GeoJSON pour les cartes (une entité = une ligne du parquet, même id_ligne) ----------
    g = m.merge(
        df[["id_ligne"]], on="id_ligne"
    )  # m porte déjà les colonnes ; on garde la géométrie
    props = ["troncon", "itineraire", "commune", "code_insee", "longueur_m", "longueur_dans_old_m",
             "part_dans_old", "ha_a_traiter", "ha_forte"]  # fmt: skip
    g = g.set_geometry("geometry")
    for c in ["longueur_m", "longueur_dans_old_m", "part_dans_old", "ha_a_traiter", "ha_forte"]:
        g[c] = df.set_index("id_ligne")[c].reindex(g["id_ligne"]).values
    g["troncon"] = g["troncon"].astype(int)
    f_velo = ecrire_geojson(g, "old_veloroutes", "id_ligne", TOL_TRONCONS_M, props)

    zone = old.copy()
    zone["id"] = zone["arrete"].map({True: "zone_arretee", False: "zone_en_attente"})
    zone["arrete_prefectoral"] = zone["dat_ap_old"].fillna("non renseigné")
    zone["libelle"] = zone["arrete"].map({True: "zone avec arrêté préfectoral (09/01/2025)",
                                          False: "zone marquée en attente de l'arrêté ministériel"})  # fmt: skip
    f_zone = ecrire_geojson(zone, "old_zone", "id", TOL_ZONE_M, ["libelle", "arrete_prefectoral"])

    communes = od.load_communes()
    concernees = communes[communes["insee_com"].isin(df["code_insee"].dropna())]
    # une fois parquet et GeoJSON écrits : le tableau par commune pour la carte choroplèthe
    par_commune = df.groupby("code_insee").agg(
        ha_a_traiter=("ha_a_traiter", "sum"), ha_forte=("ha_forte", "sum"),
        longueur_dans_old_m=("longueur_dans_old_m", "sum"),
    ).round(3)  # fmt: skip
    concernees = concernees.join(par_commune, on="insee_com")
    f_com = ecrire_geojson(concernees, "old_communes", "insee_com", TOL_COMMUNES_M,
                           ["commune", "ha_a_traiter", "ha_forte", "longueur_dans_old_m"])  # fmt: skip

    # ---- Figure de départ : où commencer ? -----------------------------------------------------
    top = (df.groupby("commune")[["ha_forte", "ha_moyenne", "ha_legere", "ha_courante"]].sum()
             .assign(total=lambda d: d.sum(axis=1)).sort_values("ha_forte", ascending=False).head(10))  # fmt: skip
    total_ha, forte_ha = df["ha_a_traiter"].sum(), df["ha_forte"].sum()
    km_total, km_old = df["longueur_m"].sum() / 1000, df["longueur_dans_old_m"].sum() / 1000
    premiere = top.index[0]
    title = (
        f"{km_old:.0f} km de véloroutes sur {km_total:.0f} traversent la zone OLD : "
        f"{total_ha:.0f} ha à débroussailler ({BANDE_M} m de chaque côté, emprise de la voie "
        f"retirée), dont {forte_ha:.0f} ha en forêt fermée. {premiere} en concentre "
        f"{top['ha_forte'].iloc[0] / forte_ha * 100:.0f}\u00a0%"
    )
    fig = go.Figure()
    for col, nom, couleur in [("ha_forte", "forêt fermée (intervention forte)", VERMILLION),
                              ("ha_moyenne", "élagage, éclaircie (moyenne)", ORANGE),
                              ("ha_legere", "débroussaillage (légère)", GREEN),
                              ("ha_courante", "entretien courant", "#BBBBBB")]:  # fmt: skip
        fig.add_bar(y=top.index, x=top[col], name=nom, orientation="h", marker_color=couleur)
    fig.update_layout(barmode="stack", yaxis={"autorange": "reversed"},
                      xaxis_title="Hectares à débroussailler le long des véloroutes",
                      legend={"orientation": "h", "y": -0.3, "font": {"size": 13}})  # fmt: skip
    style(fig, title).update_layout(margin={"b": 170})
    save_figure(fig, "old_veloroutes")

    record(
        "old_veloroutes", df, path, None,
        " ; ".join(SOURCES.values()), LICENCE, title,
        note=f"{len(df)} lignes = tronçons de véloroute × commune ({df['troncon'].nunique()} "
        "tronçons). Surfaces : hypothèses (bande, emprise, niveau d'intervention par nature de "
        "végétation), voir assumptions. Géométries : old_zone.geojson, old_veloroutes.geojson, "
        "old_communes.geojson (WGS 84, simplifiés).",
        assumptions={"BANDE_M": BANDE_M, "DISTANCE_FORET_M": DISTANCE_FORET_M,
                     "EMPRISES_m": EMPRISES, "NATURES_intervention": NATURES},
        geojson=[f.name for f in (f_zone, f_velo, f_com)],
        period_note="zonage OLD 2026-02-16 (arrêté préfectoral du 09/01/2025) ; véloroutes "
        "2025-11-21 ; bois classés 2026-02-16 ; BD TOPO IGN version en ligne le jour du build",
    )  # fmt: skip
    print(df.shape, title)
    print("km", round(km_total, 1), "dans OLD", round(km_old, 1), "ha", round(total_ha, 1),
          "forte", round(forte_ha, 1))  # fmt: skip
    for f in (f_zone, f_velo, f_com):
        print(f.name, round(f.stat().st_size / 1e6, 2), "Mo")
    print(fr(len(df)), "lignes")
