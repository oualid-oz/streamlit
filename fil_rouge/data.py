"""Exo 1 : lire mes parties d'échecs. Environ 25 min.

Question : je joue depuis 2023, je stagne, qu'est-ce que je devrais travailler ?
À produire : un DataFrame propre, prêt pour les figures de l'exo 1 et pour l'appli de l'exo 2.
Les colonnes et leurs pièges sont dans data/echecs/LISEZMOI.md : lisez-le d'abord.
Lancer : uv run python fil_rouge/data.py
"""

from pathlib import Path

import numpy as np

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "echecs"

# Colonnes de parties.csv dont le reste du fil rouge a besoin.
COLONNES_TEXTE = ["partie_id", "date_jeu", "resultat", "cadence", "couleur", "ouverture_famille"]
COLONNES_NOMBRE = ["elo_joueur", "elo_adverse", "gaffes_joueur"]
RESULTATS = {"win": "victoire", "draw": "nulle", "lose": "défaite"}
SCORES = {"victoire": 1.0, "nulle": 0.5, "défaite": 0.0}


def valider(df: pd.DataFrame) -> pd.DataFrame:
    """Plan B : s'arrêter avec un message clair si le fichier n'a pas la forme attendue.

    Colonnes absentes, colonnes entièrement vides, nombres lus comme du texte,
    identifiant de partie en double, résultat inconnu.
    """
    attendues = COLONNES_TEXTE + COLONNES_NOMBRE
    manquantes = [c for c in attendues if c not in df.columns]
    if manquantes:
        raise ValueError(f"colonnes absentes de parties.csv : {manquantes}")

    vides = [c for c in attendues if df[c].isna().all()]
    if vides:
        raise ValueError(f"colonnes entièrement vides : {vides}")

    texte = [c for c in COLONNES_NOMBRE if not pd.api.types.is_numeric_dtype(df[c])]
    if texte:
        raise ValueError(f"colonnes lues comme du texte au lieu de nombres : {texte}")

    doublons = df.loc[df["partie_id"].duplicated(), "partie_id"].unique()
    if len(doublons):
        raise ValueError(f"partie_id en double : {list(doublons[:5])}")

    inconnus = sorted(
        set(df["resultat"].dropna()) - set(RESULTATS)
        | ({"(vide)"} if df["resultat"].isna().any() else set())
    )
    if inconnus:
        raise ValueError(f"résultats inconnus (attendus {list(RESULTATS)}) : {inconnus}")

    return df


def load_data() -> pd.DataFrame:
    """Une ligne par partie (data/echecs/parties.csv), validée.

    Ajoutez : le résultat de mon point de vue en français, un score (1, 0,5 ou 0),
    l'année, l'heure, et l'écart d'Elo avec l'adversaire. Une cadence vide veut dire
    « aucune » : ne la laissez pas disparaître des filtres.
    Les exos suivants lisent ces colonnes, gardez ces noms : date_jeu (en datetime),
    resultat (victoire, nulle, défaite), score, annee, heure (UTC), ecart_elo
    (Elo de l'adversaire moins le mien), cadence.
    """
    df = valider(pd.read_csv(DATA / "parties.csv"))
    # Dates en UTC sans fuseau écrit : on les garde naïves, à lire comme de l'UTC.
    df["date_jeu"] = pd.to_datetime(df["date_jeu"])
    df["resultat"] = df["resultat"].map(RESULTATS)
    df["score"] = df["resultat"].map(SCORES)
    df["annee"] = df["date_jeu"].dt.year
    df["heure"] = df["date_jeu"].dt.hour
    # Vide pour 10 parties (Elo inconnu) : NaN, pas 0.
    df["ecart_elo"] = df["elo_adverse"] - df["elo_joueur"]
    # Une cadence vide (correspondance, sans pendule, importée) devient « aucune »,
    # sinon un filtre sur la cadence ferait disparaître ces 48 parties.
    df["cadence"] = df["cadence"].fillna("aucune")
    return df


def load_coups() -> pd.DataFrame:
    """Un de mes coups jugés mauvais par ligne (data/echecs/coups_juges.csv)."""
    coups = pd.read_csv(DATA / "coups_juges.csv")
    manquantes = {"partie_id", "phase", "jugement"} - set(coups.columns)
    if manquantes:
        raise ValueError(f"colonnes absentes de coups_juges.csv : {sorted(manquantes)}")
    return coups


def familles(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Score moyen par famille d'ouvertures, la pire d'abord.

    Colonnes : famille, n (parties), score, gaffes (par partie).
    Sous min_n parties le chiffre ne dit rien : écartez la famille.
    """
    f = (
        df.dropna(subset=["ouverture_famille"])
        .groupby("ouverture_famille")
        .agg(n=("partie_id", "nunique"), score=("score", "mean"), gaffes=("gaffes_joueur", "mean"))
        .reset_index()
        .rename(columns={"ouverture_famille": "famille"})
    )
    return f[f["n"] >= min_n].sort_values("score").reset_index(drop=True)


def load_phases() -> pd.DataFrame:
    """Une phase de partie par ligne (data/echecs/phases.csv), sans opening_theory.

    opening_theory est le début de opening : la garder compterait deux fois les mêmes coups.
    """
    phases = pd.read_csv(DATA / "phases.csv")
    return phases[phases["phase"].isin(["opening", "middlegame", "endgame"])]


def grosses_erreurs(coups: pd.DataFrame) -> pd.DataFrame:
    """Mes erreurs et gaffes d'au moins 200 cp, ou qui touchent à un mat (conseils.md, section 4)."""
    grave = coups["jugement"].isin(["mistake", "blunder"])
    lourde = (coups["variation_eval_cp"] >= 200) | (coups["mecanisme"] == "mate")
    return coups[grave & lourde]


def gaffes_par_phase(phases: pd.DataFrame) -> pd.DataFrame:
    """Mes fautes pour 100 de mes coups, par phase, la pire en gaffes d'abord.

    Le milieu de partie est le plus long : compter les gaffes sans les rapporter au nombre
    de coups le désignerait toujours. nb_coups compte ici des demi-coups des deux camps,
    la moitié sont les miens.
    Colonnes : phase, parties (qui atteignent la phase), mes_coups, gaffes, erreurs,
    imprecisions, pour_100 (gaffes), erreurs_100, imprecisions_100.
    """
    p = phases.groupby("phase").agg(
        parties=("partie_id", "nunique"),
        demi=("nb_coups", "sum"),
        gaffes=("gaffes_joueur", "sum"),
        erreurs=("erreurs_joueur", "sum"),
        imprecisions=("imprecisions_joueur", "sum"),
    )
    p["mes_coups"] = p["demi"] / 2
    p["pour_100"] = 100 * p["gaffes"] / p["mes_coups"]
    p["erreurs_100"] = 100 * p["erreurs"] / p["mes_coups"]
    p["imprecisions_100"] = 100 * p["imprecisions"] / p["mes_coups"]
    return p.drop(columns="demi").reset_index().sort_values("pour_100", ascending=False)


# Les familles de fautes de conseils.md (section 4), lues dans sous_type et mecanisme.
FAMILLES_FAUTES = {
    ("allowed_tactic", "material"): "pièce laissée en prise",
    ("missed_tactic", "material"): "gain raté",
    ("allowed_tactic", "mate"): "mat permis",
    ("missed_tactic", "mate"): "mat raté",
    ("allowed_tactic", "promotion"): "promotion permise",
    ("missed_tactic", "promotion"): "promotion ratée",
}


def chances(cp: pd.Series) -> pd.Series:
    """Chances de gain de -1 à +1, formule de Lichess (conseils.md, section 2), cp coupé à ±1 000."""
    return 2 / (1 + np.exp(-0.00368208 * cp.clip(-1000, 1000))) - 1


def perte_proba(coups: pd.DataFrame) -> pd.Series:
    """Points de probabilité de gagner perdus par mon coup (une gaffe en perd au moins 15).

    eval_cp est du point de vue des Blancs : on le retourne quand je joue les Noirs.
    L'évaluation avant mon coup est celle d'après plus ce que le coup m'a fait perdre.
    """
    apres = coups["eval_cp"].where(coups["couleur"] == "white", -coups["eval_cp"])
    avant = apres + coups["variation_eval_cp"]
    return 100 * (chances(avant) - chances(apres)) / 2


def familles_fautes(erreurs: pd.DataFrame) -> pd.DataFrame:
    """Combien de fautes par famille (pièce laissée en prise, gain raté...), la plus fréquente d'abord."""
    noms = [
        FAMILLES_FAUTES.get((s, m), "positionnelle (autre)")
        for s, m in zip(erreurs["sous_type"], erreurs["mecanisme"])
    ]
    f = pd.Series(noms, name="famille").value_counts().rename_axis("famille").reset_index(name="n")
    f["part"] = f["n"] / f["n"].sum()
    return f


def fautes_repetees(coups: pd.DataFrame, min_fois: int = 2) -> pd.DataFrame:
    """Les mêmes fautes d'ouverture rejouées : même coup, même numéro, même couleur.

    Ce sont celles qu'on peut apprendre par cœur (conseils.md, section 8).
    """
    o = coups[coups["phase"] == "opening"]
    r = (
        o.groupby(["couleur", "numero_coup", "coup"])
        .agg(
            fois=("partie_id", "nunique"),
            meilleur_coup=("meilleur_coup", lambda s: s.mode().iat[0] if s.notna().any() else ""),
            perte_cp=("variation_eval_cp", "mean"),
        )
        .reset_index()
    )
    return r[r["fois"] >= min_fois].sort_values(["fois", "perte_cp"], ascending=False)


def ouvertures_a_reparer(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """Famille et couleur qui me coûtent le plus de points, la pire d'abord.

    Comme le plan du jour de ChessXP (conseils.md, section 10), une ouverture jouée souvent et
    qui va mal passe avant une ouverture rare : points_perdus = (score moyen - score) x parties.
    """
    moyenne = df["score"].mean()
    o = (
        df.dropna(subset=["ouverture_famille"])
        .groupby(["ouverture_famille", "couleur"])
        .agg(n=("partie_id", "nunique"), score=("score", "mean"))
        .reset_index()
        .rename(columns={"ouverture_famille": "famille"})
    )
    o = o[o["n"] >= min_n]
    o["points_perdus"] = (moyenne - o["score"]) * o["n"]
    return o[o["points_perdus"] > 0].sort_values("points_perdus", ascending=False)


if __name__ == "__main__":
    d = load_data()
    print(d.shape)
    print(d[["date_jeu", "resultat", "score", "annee", "heure", "ecart_elo", "cadence"]].head())
    print(d["cadence"].value_counts())
    print(familles(d).head(10))
