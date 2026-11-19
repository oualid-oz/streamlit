"""OLD et véloroutes du Loiret : chargement des couches GéoLoiret et croisements.

Tout est mesuré en Lambert-93 (EPSG:2154), qui compte en mètres. Les couches distantes sont
téléchargées une fois dans data/cache/geoloiret/, puis relues du disque. Licence Ouverte 2.0.

Essai rapide : uv run --with geopandas python old_data.py
"""

import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

DATA = Path(__file__).parent / "data"
SHP = DATA / "old" / "ZIOLD_DEBROUSSAILLEMENT.shp"
CACHE = DATA / "cache" / "geoloiret"
L93 = 2154

ARCGIS = "https://geoloiret.loiret-numerique.fr/ags25/rest/services/"
COUCHES = {
    "veloroutes": "I_7_Reseaux_Transports/VELOROUTE/FeatureServer/4",
    "vegetation": "I_7_Reseaux_Transports/VELOROUTE_TERRAIN/FeatureServer/5",
    "bois": "III_12_Zones_a_risque_naturel/FORET_BOIS_CLASSES_RISQUE_INCENDIE/FeatureServer/44",
    "communes": "V-BDTOPO/LIMITES_ADMINISTRATIVES45/FeatureServer/3",
    "colleges": "III_2_Batiment/ETABLISSEMENTS_SCOLAIRES/FeatureServer/4",
}
ISOGEO = (
    "https://open.isogeo.com/apiquery/hostedRessources/"
    "1742fb942d7b4756b9778c3b3cbc992e/HWglEr-z4Bry_rKQOTINX9gAH4Yu0/"
)
ARCHIVES = {  # le catalogue ne sert ces trois couches qu'en shapefile zippé
    "Chemins ruraux (PDIPR)": "986a15aa66d84e5cb28b39b0d90f0c77/67306b43bfcd4e52959a88e8c1c30dc2.bin/I_7_PDIPR_CR.zip",
    "Boucles cyclotouristiques": "e64979de600b4075b488b5247acb9ea3/0c83ce3b69da44f6835512400e5e4148.bin/PDIPR_Cyclo_Boucles.zip",
    "Itinéraires de randonnée (PDIPR)": "475640b269fe4cd58cb2ac445b2777ff/696297c710fa461cad579903993501d0.bin/PDIPR_ITINERAIRES.zip",
}

DEDANS, DEHORS = "dans la zone OLD", "hors zone"
INCONNU = "non renseigné"
ITINERAIRES = {
    "EV6": "Loire à vélo",
    "EV3": "Scandibérique",
    "EV3-EV6": "Loire à vélo et Scandibérique",
    "CANAL_d_ORLEANS": "Canal d'Orléans",
    "V48": "V48 (en projet)",
}
GESTION = {
    "DEPARTEMENT DU LOIRET": "Département du Loiret",
    "COMMUNE": "Commune",
    "ETAT_VNF": "État (VNF)",
}
# Codes du schéma national des véloroutes (Vélo & Territoires) : la couche ne porte pas de libellés.
VOIES = {
    "VV": "voie verte",
    "PCY": "piste cyclable",
    "ASP": "autre site propre",
    "BCY": "bande cyclable",
    "ICA": "circulation apaisée",
    "RTE": "route",
}
REVETEMENTS = {"LIS": "lisse", "RUG": "rugueux", "MEU": "meuble"}
# avancement 04 = ouvert. Les 22 tronçons en 02 n'ont pas d'année d'ouverture : presque toute la
# V48 (« à aménager » dans les remarques) et quelques variantes.
OUVERT = "04"

# La couche ne donne pas la largeur des voies. Hypothèses en mètres, modifiables dans l'appli.
EMPRISES = {
    "voie verte": 3,
    "piste cyclable": 3,
    "autre site propre": 3,
    "bande cyclable": 6,
    "circulation apaisée": 5,
    "route": 6,
    INCONNU: 3,
}
# Zones de végétation de la BD TOPO (IGN). Une forêt fermée couvre plus de 40 % du sol, une forêt
# ouverte de 10 à 40 % : c'est la densité qu'on a. Le niveau d'intervention est une hypothèse.
IGN_WFS = "https://data.geopf.fr/wfs/ows"
MARGE_M = (
    40  # on télécharge la végétation jusqu'à 40 m des voies, au-delà de la bande la plus large
)
FORTE, MOYENNE, LEGERE, COURANT = (
    "forte (coupes, élagage sévère)",
    "moyenne (élagage, éclaircie)",
    "légère (débroussaillage)",
    "entretien courant",
)
INTENSITES = [FORTE, MOYENNE, LEGERE, COURANT]
NATURES = {
    "Forêt fermée de conifères": FORTE,
    "Forêt fermée mixte": FORTE,
    "Forêt fermée de feuillus": FORTE,
    "Bois": MOYENNE,
    "Forêt ouverte": MOYENNE,
    "Peupleraie": MOYENNE,
    "Haie": MOYENNE,
    "Lande ligneuse": LEGERE,
    "Verger": COURANT,
    "Vigne": COURANT,
}


def couche(nom: str, champs: str = "*") -> gpd.GeoDataFrame:
    """Une couche ArcGIS entière. L'API répond en GeoJSON, donc en WGS 84 : on reprojette."""
    fichier = CACHE / f"{nom}.geojson"
    if not fichier.exists():
        params = {"where": "1=1", "outFields": champs, "outSR": 4326, "f": "geojson"}
        reponse = requests.get(ARCGIS + COUCHES[nom] + "/query", params=params, timeout=180)
        reponse.raise_for_status()
        contenu = reponse.json()
        if "features" not in contenu:  # ArcGIS renvoie ses erreurs avec un code HTTP 200
            raise ValueError(f"{nom} : {contenu.get('error', contenu)}")
        if contenu.get("exceededTransferLimit"):  # l'API coupe à 2 000 entités
            raise ValueError(f"{nom} : réponse tronquée, il faut paginer avec resultOffset")
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(reponse.text, encoding="utf-8")
    return gpd.read_file(fichier).to_crs(L93)


def en_l93(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Ne reprojette que s'il le faut. Une couche déjà en Lambert-93 bougerait de quelques
    milliardièmes de mètre, assez pour sortir de la zone les 45 chemins posés sur sa limite."""
    return gdf if gdf.crs == L93 else gdf.to_crs(L93)


def archive(nom: str) -> gpd.GeoDataFrame:
    fichier = CACHE / ARCHIVES[nom].rsplit("/", 1)[1]
    if not fichier.exists():
        reponse = requests.get(ISOGEO + ARCHIVES[nom], timeout=180)
        reponse.raise_for_status()
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_bytes(reponse.content)
    return en_l93(gpd.read_file(fichier))


def propre(serie: pd.Series, libelles: dict | None = None) -> pd.Series:
    """Vide, espaces et « NEANT » deviennent « non renseigné » ; les codes prennent leur libellé."""
    s = serie.astype("string").str.strip().replace({"": pd.NA, "NEANT": pd.NA})
    if libelles:
        s = s.map(lambda v: libelles.get(v, v), na_action="ignore")
    return s.fillna(INCONNU)


def load_old() -> gpd.GeoDataFrame:
    """Deux polygones. Un seul porte la date de son arrêté préfectoral, l'autre l'attend."""
    old = en_l93(gpd.read_file(SHP))[["dat_ap_old", "geometry"]]
    old["arrete"] = old["dat_ap_old"].notna()
    return old


def load_veloroutes() -> gpd.GeoDataFrame:
    """1 473 tronçons, dont 22 pas encore ouverts au public."""
    brut = couche("veloroutes", "objectid,id_on3v,gestion,statut,revetement,avancement")
    velo = brut[["objectid", "geometry"]].rename(columns={"objectid": "troncon"})
    velo["itineraire"] = brut["id_on3v"].map(ITINERAIRES)
    if velo["itineraire"].isna().any():
        raise ValueError(f"itinéraires inconnus : {set(brut['id_on3v']) - set(ITINERAIRES)}")
    velo["gestionnaire"] = propre(brut["gestion"], GESTION)
    velo["voie"] = propre(brut["statut"], VOIES)
    velo["revetement"] = propre(brut["revetement"], REVETEMENTS)
    velo["ouvert"] = brut["avancement"] == OUVERT
    return velo


def load_communes() -> gpd.GeoDataFrame:
    return couche("communes", "nom,insee_com").rename(columns={"nom": "commune"})


def load_bois() -> gpd.GeoDataFrame:
    """1 712 bois et forêts classés à risque d'incendie. Quelques contours sont à réparer."""
    bois = couche("bois", "objectid")[["geometry"]]
    bois["geometry"] = bois.make_valid()
    return bois


def load_colleges(zone) -> gpd.GeoDataFrame:
    colleges = couche("colleges", "nom,commune,type")
    colleges["situation"] = colleges.within(zone).map({True: DEDANS, False: DEHORS})
    colleges["distance_m"] = colleges.distance(zone).round()
    return colleges


def rattacher(gdf: gpd.GeoDataFrame, communes: gpd.GeoDataFrame) -> pd.Series:
    """La commune où tombe le milieu de chaque ligne. Un tronçon fait 220 m en moyenne."""
    milieux = gpd.GeoDataFrame(geometry=gdf.interpolate(0.5, normalized=True), crs=gdf.crs)
    trouve = gpd.sjoin(milieux, communes[["commune", "geometry"]], how="left")["commune"]
    return trouve[~trouve.index.duplicated()].fillna("hors Loiret")


def croiser(velo: gpd.GeoDataFrame, zone) -> gpd.GeoDataFrame:
    """Coupe chaque tronçon en deux, la part dans la zone et la part dehors, mesurées en km."""
    morceaux = pd.concat(
        [
            velo.assign(geometry=velo.intersection(zone), situation=DEDANS),
            velo.assign(geometry=velo.difference(zone), situation=DEHORS),
        ]
    ).explode(ignore_index=True)
    morceaux["km"] = morceaux.length / 1000
    return morceaux[morceaux["km"] > 0].reset_index(drop=True)


def detailler(morceaux, communes, bois) -> gpd.GeoDataFrame:
    """Ajoute la commune, et les km du morceau qui passent sous un bois classé."""
    morceaux = morceaux.copy()
    morceaux["commune"] = rattacher(morceaux, communes)
    sous_bois = gpd.overlay(
        morceaux[["geometry"]].reset_index(names="morceau"), bois, how="intersection"
    )
    km_bois = (sous_bois.length / 1000).groupby(sous_bois["morceau"]).sum()
    morceaux["km_bois"] = km_bois.reindex(morceaux.index, fill_value=0).clip(upper=morceaux["km"])
    return morceaux


def bilan(morceaux: pd.DataFrame, par: str) -> pd.DataFrame:
    """Par itinéraire, gestionnaire, commune ou type de voie : km au total, km et part dans la zone."""
    b = morceaux.pivot_table(
        index=par, columns="situation", values="km", aggfunc="sum", fill_value=0
    ).reindex(columns=[DEDANS, DEHORS], fill_value=0)
    b["km"] = b[DEDANS] + b[DEHORS]
    b["part"] = b[DEDANS] / b["km"]
    return b.sort_values([DEDANS, "part"], ascending=False).reset_index()


def _bdtopo(table: str, bornes) -> list[dict]:
    """Les objets d'une table BD TOPO dans un rectangle, par pages de 1 000."""
    features, depart = [], 0
    while True:
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": f"BDTOPO_V3:{table}",
            "srsName": "EPSG:2154",
            "outputFormat": "application/json",
            "sortBy": "cleabs",
            "count": 1000,
            "startIndex": depart,
            "bbox": ",".join(f"{b:.0f}" for b in bornes) + ",urn:ogc:def:crs:EPSG::2154",
        }
        for essai in range(5):  # la Géoplateforme renvoie parfois une page vide : on réessaie
            reponse = requests.get(IGN_WFS, params=params, timeout=180)
            if reponse.ok and reponse.text.startswith("{"):
                break
            time.sleep(2**essai)
        else:
            raise ValueError(f"{table} : l'IGN ne répond pas ({reponse.status_code})")
        lot = reponse.json()["features"]
        features += lot
        if len(lot) < 1000:
            return features
        depart += 1000


def load_couvert(lignes: gpd.GeoDataFrame, table: str = "zone_de_vegetation") -> gpd.GeoDataFrame:
    """Une table BD TOPO (végétation, ou surfaces en eau) à moins de MARGE_M des lignes, découpée
    à cette distance. Un rectangle par groupe de tronçons voisins : la zone entière ferait des
    dizaines de milliers de polygones."""
    fichier = CACHE / f"{table}_ign.gpkg"
    if not fichier.exists():
        autour = lignes.buffer(MARGE_M).union_all()
        features = []
        for groupe in gpd.GeoSeries([autour], crs=L93).explode():
            features += _bdtopo(table, groupe.bounds)
        brut = gpd.GeoDataFrame.from_features(features, crs=L93).drop_duplicates("cleabs")
        brut["geometry"] = brut.make_valid()
        couvert = brut[["nature", "geometry"]].clip(autour).explode(ignore_index=True)
        fichier.parent.mkdir(parents=True, exist_ok=True)
        couvert[couvert.geom_type == "Polygon"].to_file(fichier)
    return gpd.read_file(fichier)


def bandes(
    dedans: gpd.GeoDataFrame, zone, largeur_m: float, emprises: dict, eau=None
) -> gpd.GeoDataFrame:
    """La bande à débroussailler de chaque côté de chaque morceau, emprise des voies retirée.

    Le tampon part du bord de la voie (axe + demi-emprise), puis on retire l'emprise de toutes
    les voies, pas seulement la sienne : aux croisements, une voie ne se débroussaille pas.
    On retire aussi l'eau (le long du canal, un côté de la bande est dans le canal) et on garde
    ce qui tombe dans la zone OLD.
    """
    demi = dedans["voie"].map(emprises).fillna(emprises[INCONNU]).astype(float) / 2
    retire = dedans.buffer(demi).union_all()
    if eau is not None and not eau.empty:
        retire = retire.union(eau.union_all())
    bande = dedans.buffer(demi + largeur_m).difference(retire).intersection(zone)
    return gpd.GeoDataFrame({"morceau": dedans.index}, geometry=bande.values, crs=dedans.crs)


def par_intensite(bandes: gpd.GeoDataFrame, couvert, natures: dict) -> gpd.GeoDataFrame:
    """Coupe chaque bande selon la végétation qu'elle traverse. Sans végétation : entretien courant.
    Deux bandes voisines se chevauchent aux jonctions : fondre par intensité avant de mesurer."""
    vegetation = couvert.assign(intensite=couvert["nature"].map(natures).fillna(COURANT))
    vegetation = vegetation[vegetation["intensite"] != COURANT][["intensite", "geometry"]]
    morceaux = gpd.overlay(bandes, vegetation, how="identity", keep_geom_type=True)
    morceaux["intensite"] = morceaux["intensite"].fillna(COURANT)
    return morceaux


def hectares(pieces: gpd.GeoDataFrame, par: str | None = None) -> pd.DataFrame:
    """Hectares par intensité (et par commune ou morceau si demandé), sans double compte."""
    if pieces.empty:
        return pd.DataFrame(0.0, index=[0] if par is None else [], columns=[*INTENSITES, "ha"])
    cles = ["intensite"] if par is None else [par, "intensite"]
    ha = pieces.dissolve(cles).area / 10_000
    t = ha.unstack("intensite") if par else ha.to_frame().T
    t = t.reindex(columns=INTENSITES).fillna(0)
    t["ha"] = t.sum(axis=1)
    return t


def load_vegetation(velo, communes, zone) -> gpd.GeoDataFrame:
    """Le relevé de terrain du Département : seules les lignes qui portent une note de travaux."""
    brut = couche("vegetation", "objectid,travaux_a_rea,date_terrain")
    notes = brut[brut["travaux_a_rea"].fillna("").str.strip() != ""].reset_index(drop=True)
    notes["travaux"] = notes["travaux_a_rea"].str.strip()
    notes["releve"] = pd.to_datetime(notes["date_terrain"], unit="ms").dt.date
    notes["km"] = notes.length / 1000
    notes["situation"] = notes.intersects(zone).map({True: DEDANS, False: DEHORS})
    notes["commune"] = rattacher(notes, communes)
    proche = gpd.sjoin_nearest(notes[["geometry"]], velo[["itineraire", "geometry"]])
    notes["itineraire"] = proche[~proche.index.duplicated()]["itineraire"]
    return notes[["itineraire", "commune", "situation", "travaux", "releve", "km", "geometry"]]


def autres_chemins(zone) -> pd.DataFrame:
    """Les autres réseaux du catalogue, croisés avec la même zone. Les boucles se recouvrent.

    Un chemin posé sur la limite de la zone compte dedans (9 km de chemins ruraux).
    """
    lignes = []
    for nom in ARCHIVES:
        chemins = archive(nom)
        km, dedans = chemins.length.sum() / 1000, chemins.intersection(zone).length.sum() / 1000
        lignes.append({"reseau": nom, "km": km, DEDANS: dedans, "part": dedans / km})
    return pd.DataFrame(lignes)


if __name__ == "__main__":
    old = load_old()
    zone = old.union_all()
    m = detailler(croiser(load_veloroutes(), zone), load_communes(), load_bois())
    for par in ["itineraire", "gestionnaire", "voie"]:
        print(bilan(m, par).round(3).to_string(index=False), "\n")
    print(bilan(m, "commune").head(5).round(3).to_string(index=False))
    print("sous un bois classé :", round(m["km_bois"].sum(), 1), "km")
    dedans = m[m["situation"] == DEDANS]
    couvert, eau = load_couvert(dedans), load_couvert(dedans, "surface_hydrographique")
    print(couvert["nature"].value_counts().to_string(), "\n")
    print(eau["nature"].value_counts().to_string(), "\n")
    for retirer in [None, eau]:
        b = bandes(dedans, zone, 10, EMPRISES, retirer)
        pieces = par_intensite(b, couvert, NATURES)
        print("bande de 10 m, eau", "retirée" if retirer is not None else "comptée")
        print(hectares(pieces).round(1).to_string(), "\n")
    print(autres_chemins(zone).round(3).to_string(index=False))
