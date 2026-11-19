# Les tips, dans l'ordre de la journée

Un assistant de code écrit mieux quand il lit la bonne documentation. Chaque tip ci-dessous ajoute une
source ou un outil au bon moment, et chaque exo se termine de la même façon : vous expliquez les lignes
que l'assistant a écrites, ligne par ligne. Les URL et les commandes ont été vérifiées le 17 novembre 2026.

## Exo 1, lire mes parties (environ 25 min)

Donnez à l'assistant `data/echecs/LISEZMOI.md` et `data/echecs/conseils.md` avant sa première question.
Le premier décrit chaque colonne et ses pièges, le second explique comment ChessXP juge un coup.
Sans eux, il invente le sens des colonnes.

- Plotly Express : https://plotly.com/python/plotly-express/
- Les graphiques en barres : https://plotly.com/python/bar-charts/
- Toute la référence : https://plotly.com/python-api-reference/
- L'index de la doc Plotly pour un assistant : https://plotly.com/llms.txt

## Exo 2, Streamlit (environ 1 h)

La doc Streamlit existe en Markdown : ajoutez `.md` à l'URL d'une page.

- Un exemple : https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart.md
- Le cache : https://docs.streamlit.io/develop/concepts/architecture/caching.md
- L'index de toute la doc : https://docs.streamlit.io/llms.txt

Collez l'URL `.md` de la page dont vous avez besoin dans votre demande, ou donnez l'index `llms.txt`
et laissez l'assistant choisir la page.

Streamlit fournit aussi des skills, des instructions écrites pour les assistants, accordées à la version
installée :

```bash
uv run streamlit skills --yes
```

La commande crée `.agents/skills/` et `.claude/skills/` dans le projet. Présentation : https://streamlit.io/agents

Un dernier réflexe : demandez deux versions d'un même morceau, gardez-en une et dites pourquoi.

## Exo 3, mise en ligne (environ 25 min)

Rien de nouveau à donner à l'assistant. Les réglages se font sur https://share.streamlit.io : votre
dépôt, la branche `main`, le fichier d'entrée `fil_rouge/app_streamlit.py`.

## Exo 4, Dash (environ 25 min)

Le fichier `AGENTS.md` à la racine de ce dépôt est la base fournie par Plotly pour les assistants de
code Dash, avec la liste des erreurs que les assistants font le plus souvent. Claude Code le lit tout
seul quand le dépôt n'a pas de `CLAUDE.md` (https://code.claude.com/docs/en/memory.md). Les autres
assistants lisent aussi `AGENTS.md`.

Comme pour Streamlit, la doc Dash a un index et des pages en Markdown :

- L'index : https://dash.plotly.com/llms.txt
- Un exemple, les callbacks : https://dash.plotly.com/basic-callbacks.md
- Le guide de Plotly pour les assistants : https://dash.plotly.com/ai-coding-assistants.md

Faites la même demande avec et sans `AGENTS.md`, et comparez le code obtenu.

## Exo 5, l'API et l'appli qui l'appelle (environ 45 min)

FastAPI n'a ni `llms.txt` ni pages en `.md`. Collez l'adresse de la page ou son contenu.

- Le tutoriel : https://fastapi.tiangolo.com/tutorial/
- Les paramètres de requête : https://fastapi.tiangolo.com/tutorial/query-params/
- Les valider (bornes, `Query`) : https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
- Côté appli, `requests` : https://requests.readthedocs.io/en/latest/user/quickstart/
- Bonus `/predict`, le corps d'une requête avec Pydantic : https://fastapi.tiangolo.com/tutorial/body/

Une fois l'API lancée, la page `http://127.0.0.1:8000/docs` liste vos routes et vous laisse les essayer.
Collez-la dans votre demande quand vous écrivez `app_api.py`.

## Exo 6, MCP (environ 20 min)

MCP est le protocole par lequel un LLM appelle des outils. Le LLM est le client, votre code est le
serveur. Introduction : https://modelcontextprotocol.io/ et le SDK Python
https://github.com/modelcontextprotocol/python-sdk

### Brancher une appli Streamlit

L'API agent est désactivée par défaut. Relancez l'appli avec l'adresse locale, sinon elle est ouverte à
tout le réseau de la salle :

```bash
uv run streamlit run fil_rouge/app_streamlit.py --server.enableAgentApi=true --server.address 127.0.0.1
```

Puis, dans un autre terminal :

```bash
claude mcp add --transport http echecs-streamlit http://127.0.0.1:8501/_stcore/agent/mcp
```

La doc : https://docs.streamlit.io/develop/concepts/ai-agents/agent-access

### Brancher une appli Dash

Passez `enable_mcp=True` au constructeur : `Dash(__name__, enable_mcp=True)`. Le serveur MCP répond sur
`/_mcp`.

```bash
claude mcp add --transport http echecs-dash http://127.0.0.1:8050/_mcp
```

La doc : https://dash.plotly.com/dash-mcp.md

### Brancher votre propre serveur

Un serveur HTTP se branche avec son URL, un serveur stdio avec la commande qui le lance (après `--`) :

```bash
claude mcp add --transport http <nom> <url>
claude mcp add --transport stdio <nom> -- uv run --directory <chemin du dépôt> python fil_rouge/mcp_server.py
```

Pour passer l'adresse de votre API au serveur : `-e AWP_API_URL=http://127.0.0.1:8000`, avant le `--`.
`claude mcp list` montre les serveurs connus, `claude mcp remove <nom>` en retire un.
La doc complète : https://code.claude.com/docs/en/mcp.md

### Local ou en ligne : qui peut joindre votre serveur ?

Le client doit pouvoir joindre le serveur. Un client sur votre poste (Claude Code, Cursor, VS Code,
Claude Desktop) joint `127.0.0.1` : rien à déployer, et c'est le seul cas où un serveur stdio marche.
Un client dans le cloud (connecteurs de claude.ai, ChatGPT) se connecte depuis les serveurs de
l'éditeur : il lui faut une URL publique en HTTPS, port 443. `127.0.0.1` et stdio n'y marchent jamais.

- Votre serveur en HTTP : `MCP_TRANSPORT=http uv run python fil_rouge/mcp_server.py`, sur `http://127.0.0.1:8001/mcp`.
- Pour une démo sans déployer, un tunnel donne une URL publique temporaire :
  `MCP_TUNNEL=1 MCP_TRANSPORT=http uv run python fil_rouge/mcp_server.py`, puis `npx localtunnel --port 8001`
  (`MCP_TUNNEL=1` : FastMCP accepte alors le nom d'hôte du tunnel).
- Sur un hébergeur (Render, Cloud Run), la variable `PORT` est fixée : le serveur écoute alors sur `0.0.0.0:$PORT`.
  Sans authentification, n'importe qui avec l'URL appelle vos outils.
- L'appli Streamlit déployée sur Community Cloud (avec `enableAgentApi = true` dans `.streamlit/config.toml`) :
  le serveur MCP est sur `https://<appli>.streamlit.app/~/+/_stcore/agent/mcp`. Sans `/~/+`, la plateforme
  répond par sa page de connexion. L'appli est publique, son API agent aussi.

Un LLM choisit un outil d'après son nom, sa docstring et ses arguments. Si l'outil est mal choisi, relisez
d'abord la docstring.
