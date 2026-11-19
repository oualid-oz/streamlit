"""Exo 2 : l'appli Streamlit du fil rouge. Environ 1 h.

Question : l'appli que ce joueur ouvrirait chaque semaine pour savoir quoi travailler.
À produire : une barre latérale (cadence, période, couleur), trois st.metric, deux figures
en colonnes. Le titre de la page dit la question, pas « Dashboard ».
Colonnes utilisées : cadence (dont « aucune »), date_jeu (datetime), couleur (white ou black),
score, gaffes_joueur. Si votre load_data() ne les donne pas ainsi, corrigez-la.
Lancer : uv run streamlit run fil_rouge/app_streamlit.py --server.address 127.0.0.1
"""

import plotly.express as px
import streamlit as st

from data import (
    familles_fautes,
    perte_proba,
    fautes_repetees,
    familles,
    gaffes_par_phase,
    grosses_erreurs,
    load_coups,
    load_data,
    load_phases,
    ouvertures_a_reparer,
)

st.set_page_config(page_title="Mes parties d'échecs", layout="wide")
print("relance")  # regardez le terminal à chaque clic

PHASES = {"opening": "ouverture", "middlegame": "milieu de jeu", "endgame": "finale"}
COULEURS = {"Toutes": None, "Blancs": "white", "Noirs": "black"}
EN_FRANCAIS = {"white": "les Blancs", "black": "les Noirs"}


# 1. Charger les données une seule fois : les relances suivantes lisent le cache.
@st.cache_data
def charger():
    return load_data(), load_coups(), load_phases()


df, coups, phases = charger()

# 2. Le titre, puis la barre latérale
st.title("Qu'est-ce que je devrais travailler cette semaine ?")

with st.sidebar:
    cadences = sorted(df["cadence"].unique())
    cadence = st.pills("Cadence", cadences, selection_mode="multi", default=cadences, key="cadence")
    debut, fin = df["date_jeu"].min().date(), df["date_jeu"].max().date()
    periode = st.date_input(
        "Période", value=(debut, fin), min_value=debut, max_value=fin, key="periode"
    )
    couleur = st.segmented_control("Couleur", list(COULEURS), default="Toutes", key="couleur")
    n_min = st.slider("Parties minimum par ouverture", 5, 100, 30, step=5, key="n_min")

# 3. Filtrer, avec un message clair quand il ne reste rien
if len(periode) != 2:
    st.warning("Choisissez la seconde date de la période.")
    st.stop()

jours = df["date_jeu"].dt.date
vue = df[df["cadence"].isin(cadence) & jours.between(*periode)]
if COULEURS.get(couleur):
    vue = vue[vue["couleur"] == COULEURS[couleur]]

if vue.empty:
    st.warning("Aucune partie pour ces filtres. Élargissez la période ou ajoutez une cadence.")
    st.stop()

# La réponse à la question du titre, calculée sur les parties filtrées
st.subheader("Mes trois chantiers")
st.caption(f"Calculés sur les {len(vue)} parties choisies dans la barre latérale.")
tactique, phase, ouverture = st.columns(3)

with tactique.container(border=True, height="stretch"):
    ge = grosses_erreurs(coups[coups["partie_id"].isin(vue["partie_id"])])
    if ge.empty:
        st.markdown("**:material/check_circle: Aucune grosse erreur sur ces parties.**")
    else:
        part_tactique = (ge["categorie"] == "tactical").mean()
        part_laissee = (ge["sous_type"] == "allowed_tactic").mean()
        part_ratee = (ge["sous_type"] == "missed_tactic").mean()
        st.markdown("**:material/swords: 1. La tactique**")
        st.metric("de mes grosses erreurs sont tactiques", f"{part_tactique:.0%}")
        if part_laissee >= part_ratee:
            st.markdown(
                f"Surtout des tactiques **laissées à l'adversaire** ({part_laissee:.0%}), "
                f"plus que des gains ratés ({part_ratee:.0%}). Avant chaque coup : "
                "« qu'est-ce que ce coup lui permet ? » (prises, échecs, fourchettes)."
            )
        else:
            st.markdown(
                f"Surtout des **gains ratés** ({part_ratee:.0%}), plus que des tactiques "
                f"laissées ({part_laissee:.0%}). Problèmes tactiques : chercher d'abord "
                "les prises et les échecs."
            )

        with st.expander("Détails", icon=":material/info:"):
            st.markdown(f"**Les {len(ge)} grosses erreurs, par famille**")
            st.dataframe(
                familles_fautes(ge),
                hide_index=True,
                column_config={
                    "n": "fautes",
                    "part": st.column_config.ProgressColumn(
                        "part", min_value=0, max_value=1, format="percent"
                    ),
                },
                alt="Grosses erreurs par famille de faute",
            )
            avec_pendule = ge.dropna(subset=["temps_restant_s"])
            if not avec_pendule.empty:
                presse = (avec_pendule["temps_restant_s"] < 30).mean()
                st.caption(
                    f"{presse:.0%} de ces erreurs sont jouées avec moins de 30 s à la pendule : "
                    + (
                        "le manque de temps en explique une bonne part."
                        if presse >= 0.3
                        else "le manque de temps n'en explique qu'une petite part."
                    )
                )
            # « perdue » à -300 cp ou moins (conseils.md, section 9), « gagnante » à +300 ou plus
            apres = ge["eval_cp"].where(ge["couleur"] == "white", -ge["eval_cp"])
            retournees = ((apres + ge["variation_eval_cp"] >= 300) & (apres <= -300)).sum()
            st.markdown(
                f"**{retournees} fois, un seul coup m'a fait passer d'une position gagnante "
                "(+300 cp) à perdue (-300 cp).**"
            )
            st.markdown("**Mes 5 erreurs qui ont coûté le plus de chances de gagner**")
            pires = (
                ge.assign(perte=perte_proba(ge), connu=ge["meilleur_coup"].notna())
                .sort_values(["perte", "connu", "variation_eval_cp"], ascending=False)
                .head(5)
                .merge(vue[["partie_id", "date_jeu"]], on="partie_id")
            )
            st.dataframe(
                pires[["date_jeu", "numero_coup", "couleur", "coup", "meilleur_coup", "perte"]],
                hide_index=True,
                column_config={
                    "date_jeu": st.column_config.DateColumn("date", format="D MMM YYYY"),
                    "numero_coup": "coup n°",
                    "coup": "joué",
                    "meilleur_coup": "meilleur",
                    "perte": st.column_config.NumberColumn(
                        "chances perdues",
                        format="%.0f pts",
                        help="points de probabilité de gagner perdus par le coup (formule Lichess)",
                    ),
                },
                alt="Les cinq erreurs qui m'ont fait perdre le plus de chances de gagner",
            )

with phase.container(border=True, height="stretch"):
    gp = gaffes_par_phase(phases[phases["partie_id"].isin(vue["partie_id"])])
    if gp["gaffes"].sum() == 0:
        st.markdown("**:material/check_circle: Aucune gaffe sur ces parties.**")
    else:
        pire, autres = gp.iloc[0], gp.iloc[1:]
        nom = PHASES[pire["phase"]]
        st.markdown(
            f"**:material/timeline: 2. Le {nom}**"
            if nom != "finale"
            else "**:material/timeline: 2. La finale**"
        )
        st.metric(f"gaffes pour 100 de mes coups en {nom}", f"{pire['pour_100']:.1f}")
        comparaison = ", ".join(
            f"{r['pour_100']:.1f} en {PHASES[r['phase']]}" for _, r in autres.iterrows()
        )
        st.markdown(
            f"Contre {comparaison}. Rapporté au nombre de coups, c'est là que je gaffe "
            "le plus : c'est la phase à revoir dans mes parties perdues."
        )

        with st.expander("Détails", icon=":material/info:"):
            st.markdown("**Mes fautes pour 100 de mes coups, par phase**")
            d = gp.assign(phase=gp["phase"].map(PHASES))
            st.dataframe(
                d[["phase", "parties", "pour_100", "erreurs_100", "imprecisions_100", "gaffes"]],
                hide_index=True,
                column_config={
                    "parties": st.column_config.NumberColumn(
                        "parties", help="parties qui atteignent cette phase"
                    ),
                    "pour_100": st.column_config.NumberColumn("gaffes", format="%.1f"),
                    "erreurs_100": st.column_config.NumberColumn("erreurs", format="%.1f"),
                    "imprecisions_100": st.column_config.NumberColumn(
                        "imprécisions", format="%.1f"
                    ),
                    "gaffes": st.column_config.NumberColumn("gaffes (total)"),
                },
                alt="Gaffes, erreurs et imprécisions pour 100 coups, par phase",
            )
            st.caption(
                "Seuils ChessXP : une imprécision fait perdre 5 points de probabilité de gagner, "
                "une erreur 10, une gaffe 15. Source : phases.csv (sans opening_theory, "
                "qui est le début de l'ouverture)."
            )

with ouverture.container(border=True, height="stretch"):
    ar = ouvertures_a_reparer(vue, n_min)
    if ar.empty:
        st.markdown(
            f"**:material/check_circle: Aucune ouverture jouée {n_min} fois ou plus "
            "ne fait baisser mon score.**"
        )
    else:
        o = ar.iloc[0]
        st.markdown(f"**:material/menu_book: 3. {o['famille']} avec {EN_FRANCAIS[o['couleur']]}**")
        st.metric(
            f"score sur {o['n']} parties",
            f"{o['score']:.2f}",
            delta=f"{o['score'] - vue['score'].mean():+.2f} vs ma moyenne",
        )
        st.markdown(
            f"L'ouverture qui me coûte le plus : à ma moyenne, j'aurais marqué environ "
            f"**{o['points_perdus']:.0f} points de plus** (une victoire = 1 point). "
            "Revoir les lignes où je refais les mêmes fautes."
        )

        with st.expander("Détails", icon=":material/info:"):
            st.markdown("**Les ouvertures qui me coûtent le plus**")
            st.dataframe(
                ar.head(5).assign(couleur=ar["couleur"].map({"white": "Blancs", "black": "Noirs"})),
                hide_index=True,
                column_config={
                    "n": "parties",
                    "score": st.column_config.NumberColumn("score", format="%.2f"),
                    "points_perdus": st.column_config.NumberColumn(
                        "points perdus", format="%.1f", help="(ma moyenne - score) × parties"
                    ),
                },
                alt="Les cinq couples ouverture et couleur qui me coûtent le plus de points",
            )
            ids = vue.loc[
                (vue["ouverture_famille"] == o["famille"]) & (vue["couleur"] == o["couleur"]),
                "partie_id",
            ]
            rep = fautes_repetees(coups[coups["partie_id"].isin(ids)])
            st.markdown(f"**Les fautes que je rejoue en {o['famille']}**")
            if rep.empty:
                st.caption(
                    f"Aucune faute d'ouverture rejouée deux fois en {o['famille']}. "
                    "Celles que je rejoue le plus, toutes ouvertures confondues :"
                )
                rep = fautes_repetees(coups[coups["partie_id"].isin(vue["partie_id"])])
            if not rep.empty:
                st.dataframe(
                    rep.head(5).assign(
                        couleur=rep["couleur"].map({"white": "Blancs", "black": "Noirs"})
                    )[["couleur", "numero_coup", "coup", "meilleur_coup", "fois", "perte_cp"]],
                    hide_index=True,
                    column_config={
                        "numero_coup": "coup n°",
                        "coup": "joué",
                        "meilleur_coup": "à jouer",
                        "fois": "parties",
                        "perte_cp": st.column_config.NumberColumn("perte moy. (cp)", format="%d"),
                    },
                    alt=f"Fautes d'ouverture répétées en {o['famille']}",
                )
                st.caption("Le même coup au même moment, plusieurs fois : la ligne à apprendre.")

st.divider()

# 4. Trois chiffres
a, b, c = st.columns(3)
a.metric("Parties", f"{len(vue):,}".replace(",", " "), border=True)
b.metric("Score moyen", f"{vue['score'].mean():.2f}", border=True)
c.metric("Gaffes par partie", f"{vue['gaffes_joueur'].mean():.2f}", border=True)

# 5. Les deux figures de l'exo 1, sur les parties filtrées
gauche, droite = st.columns(2)

famille_choisie = None
with gauche:
    f = familles(vue, n_min)
    if f.empty:
        st.info(f"Aucune famille d'ouvertures n'a {n_min} parties ou plus avec ces filtres.")
    else:
        fig1 = px.bar(
            f,
            x="score",
            y="famille",
            orientation="h",
            hover_data=["n", "gaffes"],
            title=f"{f['famille'].iloc[0]} est mon ouverture la moins rentable",
        )
        fig1.update_yaxes(autorange="reversed", title=None)
        fig1.update_xaxes(range=[0, 1], title="score moyen (1 = victoire, 0,5 = nulle)")
        # Bonus : un clic sur une barre relance l'appli et renvoie la barre choisie
        clic = st.plotly_chart(
            fig1, on_select="rerun", selection_mode="points", key="familles_clic"
        )
        points = clic.selection.points
        famille_choisie = points[0]["y"] if points else None

with droite:
    gaffes = coups[coups["partie_id"].isin(vue["partie_id"]) & (coups["jugement"] == "blunder")]
    g = (
        gaffes["phase"]
        .map(PHASES)
        .value_counts()
        .reindex(list(PHASES.values()), fill_value=0)
        .rename_axis("phase")
        .reset_index(name="gaffes")
    )
    if g["gaffes"].sum() == 0:
        st.info("Aucune gaffe sur ces parties.")
    else:
        pire = g.loc[g["gaffes"].idxmax(), "phase"]
        fig2 = px.bar(g, x="phase", y="gaffes", title=f"La plupart de mes gaffes tombent en {pire}")
        st.plotly_chart(fig2)

# Bonus : le détail de la famille cliquée
st.divider()
if famille_choisie is None:
    st.caption("Cliquez sur une barre des familles d'ouvertures pour en voir le détail.")
else:
    parties = vue[vue["ouverture_famille"] == famille_choisie]
    st.subheader(f"{famille_choisie} : le détail")

    a, b, c = st.columns(3)
    a.metric(
        "Parties",
        len(parties),
        delta=f"{len(parties) / len(vue):.0%} de toutes",
        delta_color="off",  # une part, ni bien ni mal
        delta_arrow="off",
        border=True,
    )
    b.metric(
        "Score moyen",
        f"{parties['score'].mean():.2f}",
        delta=f"{parties['score'].mean() - vue['score'].mean():+.2f} vs toutes",
        border=True,
    )
    c.metric(
        "Gaffes par partie",
        f"{parties['gaffes_joueur'].mean():.2f}",
        delta=f"{parties['gaffes_joueur'].mean() - vue['gaffes_joueur'].mean():+.2f} vs toutes",
        delta_color="inverse",  # plus de gaffes, c'est moins bien
        border=True,
    )

    variantes, dernieres = st.columns(2)
    with variantes:
        v = (
            parties.groupby(["ouverture_nom", "couleur"])
            .agg(parties=("partie_id", "nunique"), score=("score", "mean"))
            .reset_index()
            .sort_values("parties", ascending=False)
        )
        st.dataframe(
            v,
            hide_index=True,
            column_config={
                "ouverture_nom": "variante",
                "score": st.column_config.ProgressColumn(
                    "score", min_value=0, max_value=1, format="%.2f"
                ),
            },
            alt=f"Variantes de {famille_choisie} : parties et score par couleur",
        )
    with dernieres:
        st.dataframe(
            parties.sort_values("date_jeu", ascending=False)[
                ["date_jeu", "cadence", "couleur", "resultat", "ecart_elo", "gaffes_joueur"]
            ].head(20),
            hide_index=True,
            column_config={
                "date_jeu": st.column_config.DatetimeColumn(
                    "date (UTC)", format="D MMM YYYY, HH:mm"
                ),
                "ecart_elo": "écart d'Elo",
                "gaffes_joueur": "gaffes",
            },
            alt=f"Les 20 dernières parties en {famille_choisie}",
        )
