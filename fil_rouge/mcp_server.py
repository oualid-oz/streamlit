"""Exo 6 : votre propre serveur MCP. Environ 20 min.

Question : un LLM doit pouvoir interroger mes parties.
À produire : un serveur FastMCP de deux ou trois outils au-dessus de votre API (api.py doit
tourner). Le LLM choisit un outil d'après son nom, sa docstring et ses arguments : soignez-les.
Lancer : uv run python fil_rouge/mcp_server.py   (stdio : c'est le client LLM qui le lance,
voir contexte/README.md pour le brancher). Lancé à la main, il n'affiche rien et attend un
client : c'est normal. Pour tester : npx @modelcontextprotocol/inspector uv run python fil_rouge/mcp_server.py
"""

import os

import requests  # noqa: F401
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

API = os.environ.get("AWP_API_URL", "http://127.0.0.1:8000")
# Deux transports. stdio (par défaut) : le client LLM lance ce script lui-même, sur la même machine.
# MCP_TRANSPORT=http : un serveur HTTP sur /mcp, pour un client qui ne lance pas le script (un client
# dans le cloud, via un hébergeur ou un tunnel). En local : 127.0.0.1:8001 (l'API est sur 8000), pas
# ouvert à la salle. Sur un hébergeur qui fixe $PORT (Render, Cloud Run) : 0.0.0.0:$PORT.
HTTP = os.environ.get("MCP_TRANSPORT") == "http"
HOTE = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
# En local, FastMCP refuse un nom d'hôte autre que 127.0.0.1 ou localhost (protection contre le DNS
# rebinding). Derrière un tunnel (MCP_TUNNEL=1), l'hôte est celui du tunnel : on lève la protection,
# le serveur est de toute façon public tant que le tunnel tourne.
TUNNEL = os.environ.get("MCP_TUNNEL") == "1"
SECU = TransportSecuritySettings(enable_dns_rebinding_protection=False) if TUNNEL else None
mcp = FastMCP("echecs", host=HOTE, port=int(os.environ.get("PORT", "8001")), transport_security=SECU)

# TODO 1. Une fonction qui appelle l'API et lève une erreur si la réponse n'est pas un succès
# TODO 2. @mcp.tool() : mes pires ouvertures pour une cadence (GET /ouvertures). Typez cadence avec
#         Literal["bullet", "blitz", "rapid"] : le LLM voit alors les valeurs permises
# TODO 3. @mcp.tool() : mes chances de victoire dans une situation donnée (POST /predict, si vous avez fait le bonus)

if __name__ == "__main__":
    # Derrière un tunnel : MCP_TUNNEL=1 MCP_TRANSPORT=http uv run python …, puis npx localtunnel --port 8001
    mcp.run(transport="streamable-http" if HTTP else "stdio")
