# AWP : applications web de données avec Python

CODA Orléans, M2-D, jeudi 19 et vendredi 20 novembre 2026.

Sur cette page, **Use this template** → **Create a new repository**, en public : c'est sur
votre copie que vous pousserez à l'exo 3. Puis :

```bash
git clone https://github.com/<votre-compte>/<votre-copie>
cd <votre-copie>
uv sync
uv run pytest -q     # 2 passed, 2 skipped : les données se lisent, le reste est à faire
```

## Jeudi, le fil rouge : mes parties d'échecs

Le jeu de données est celui d'un joueur, exporté de ChessXP et anonymisé : `data/echecs/`.
Lisez d'abord `data/echecs/LISEZMOI.md` (une section par fichier, les colonnes et leurs pièges), puis
`data/echecs/conseils.md` (comment ChessXP juge un coup). La question de la journée : « je joue depuis
2023, je stagne, qu'est-ce que je devrais travailler ? » Vous n'avez pas besoin de savoir jouer.

Les fichiers de `fil_rouge/` sont des squelettes : un énoncé en tête, des `TODO`, pas de solution.

| Exo | Durée | Fichier | Lancer |
|---|---|---|---|
| 1 | environ 25 min | `fil_rouge/data.py`, `fil_rouge/01_figures.py` | `uv run python fil_rouge/01_figures.py` |
| 2 | environ 1 h | `fil_rouge/app_streamlit.py` | `uv run streamlit run fil_rouge/app_streamlit.py --server.address 127.0.0.1` |
| 3 | environ 25 min | le même, en ligne | share.streamlit.io, fichier d'entrée `fil_rouge/app_streamlit.py` |
| 4 | environ 25 min | `fil_rouge/app_dash.py` | `uv run python fil_rouge/app_dash.py` |
| 5 | environ 45 min | `fil_rouge/api.py`, puis `fil_rouge/app_api.py` (ou votre appli de l'exo 2 ou 4) ; bonus : `/predict` et `client.py` | `uv run uvicorn api:app --app-dir fil_rouge --host 127.0.0.1 --port 8000 --reload`, puis, dans un second terminal, `uv run streamlit run fil_rouge/app_api.py --server.address 127.0.0.1` |
| 6 | environ 20 min | l'appli de l'exo 2, puis `fil_rouge/mcp_server.py` | `uv run streamlit run fil_rouge/app_streamlit.py --server.enableAgentApi=true --server.address 127.0.0.1`, puis `uv run python fil_rouge/mcp_server.py` (en HTTP : `MCP_TRANSPORT=http uv run python fil_rouge/mcp_server.py`, sur `http://127.0.0.1:8001/mcp`) |

`contexte/README.md` : les tips, dans l'ordre de la journée (documentation en Markdown, `llms.txt`,
`streamlit skills`, brancher un serveur MCP). Chaque exo se termine par la lecture du code que
l'assistant a écrit : vous expliquez les lignes.

Bloqué : la branche `solutions` de ce dépôt contient le fil rouge terminé. Votre copie ne la
suit pas, ajoutez ce dépôt comme second remote, une seule fois :

```bash
git remote add prof https://github.com/jlkhermes38/awp-gabarit
git fetch prof
```

Puis récupérez les fichiers de l'exo où vous êtes bloqué. Les solutions s'appuient sur
`data.py` et `figures.py` : un seul fichier ne suffit pas. Ces fichiers remplacent les vôtres,
commitez votre travail avant.

| Exo | Commande |
|---|---|
| 1 | `git checkout prof/solutions -- fil_rouge/data.py fil_rouge/figures.py fil_rouge/01_figures.py` |
| 2 et 3 | `git checkout prof/solutions -- fil_rouge/data.py fil_rouge/figures.py fil_rouge/app_streamlit.py` |
| 4 | `git checkout prof/solutions -- fil_rouge/data.py fil_rouge/figures.py fil_rouge/app_dash.py` |
| 5 | `git checkout prof/solutions -- fil_rouge/data.py fil_rouge/api.py fil_rouge/app_api.py fil_rouge/client.py` |
| 6 | `git checkout prof/solutions -- fil_rouge/mcp_server.py` (l'API de l'exo 5 doit tourner) |

`AGENTS.md` est la base Dash fournie par Plotly, pour votre assistant de code.

## Vendredi, le projet

- `data/projets/` : un ou plusieurs Parquet par cas, huit cas en tout, et des GeoJSON pour les cartes des cas 1 et 2. **Tout est dans [`data/projets/LISEZMOI.md`](data/projets/LISEZMOI.md)** : fichiers, lignes, périodes, colonnes, sources et licences. Une ligne réelle par fichier dans `summary.json`
- `projet/cas/` : **une page par cas** ([index](projet/cas/README.md)) : le contexte, qui décide quoi, les colonnes expliquées, les pièges et des questions métier possibles
- `projet/app.py` : le point de départ, `uv run streamlit run projet/app.py --server.address 127.0.0.1`
- `projet/llm.py` : un client compatible OpenAI (Ollama, Groq, Google AI Studio). Copiez `.streamlit/secrets.toml.example` en `.streamlit/secrets.toml`, jamais versionné
- `tests/test_app.py` : les tests du dépôt, `uv run pytest -q`
- `sources/` : les scripts qui ont construit `data/projets/`, et l'adresse exacte de chaque source, couches du Loiret comprises ([`sources/README.md`](sources/README.md))

| Cas | Fichier | Source | Licence |
|---|---|---|---|
| OLD et véloroutes | [`old_veloroutes.parquet`](data/projets/old_veloroutes.parquet) + 3 GeoJSON | [GéoLoiret](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm) | Licence Ouverte 2.0, « Source : Département du Loiret » |
| Collèges et risques | [`colleges_risques.parquet`](data/projets/colleges_risques.parquet), avec `colleges`, `risques_communes`, `risques_catnat` et 2 GeoJSON | [GéoLoiret](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm), [data.education.gouv.fr](https://data.education.gouv.fr), [Géorisques](https://www.georisques.gouv.fr/) | Licence Ouverte 2.0 |
| Énergie | [`energie.parquet`](data/projets/energie.parquet) | [RTE, éCO2mix régional](https://opendata.reseaux-energies.fr/explore/dataset/eco2mix-regional-cons-def/) | Licence Ouverte 2.0 |
| Sécurité routière | [`securite_routiere.parquet`](data/projets/securite_routiere.parquet) | [ONISR, accidents corporels](https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2025/) | Licence Ouverte 2.0 |
| Immobilier | [`immobilier.parquet`](data/projets/immobilier.parquet) | [DVF géolocalisées](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/) | Licence Ouverte 2.0 |
| Location courte durée | [`airbnb_lyon.parquet`](data/projets/airbnb_lyon.parquet), [`airbnb_lyon_reviews.parquet`](data/projets/airbnb_lyon_reviews.parquet) | [Inside Airbnb](https://insideairbnb.com/get-the-data/) | CC BY 4.0 |
| E-commerce | [`olist.parquet`](data/projets/olist.parquet), [`olist_commentaires_negatifs.parquet`](data/projets/olist_commentaires_negatifs.parquet) | [Olist sur Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | CC BY-NC-SA 4.0 |
| Territoire du Loiret | [`territoire_loiret.parquet`](data/projets/territoire_loiret.parquet) | [Département du Loiret](https://www.data.gouv.fr/organizations/departement-du-loiret/) | Licence Ouverte 2.0 |

Un cas peut être pris par deux groupes, à condition que leurs décisions diffèrent. Vous pouvez aussi apporter votre propre jeu de données (licence qui permet la réutilisation, moins de 50 Mo, aucune donnée personnelle), ou des données de votre entreprise : l'accord écrit de votre tuteur, des données anonymisées, un dépôt GitHub privé partagé avec moi, et une URL publique qui ne montre qu'un échantillon anonymisé ou des données fictives de même forme. Aucune donnée d'entreprise n'est envoyée à une API de LLM externe sans accord : sinon, Ollama en local. Je valide au cadrage de vendredi 9h45.