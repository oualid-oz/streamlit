"""Exo 4 : la même appli en Dash, avec un drill-down. Environ 25 min.

Question : quelles ouvertures coûtent des points, et dans quelles parties ?
À produire : un curseur (parties minimum) et le graphique des familles ; un clic sur une barre
liste les parties, un clic sur une partie liste les coups jugés mauvais, dans deux AG Grid.
Lancer : uv run python fil_rouge/app_dash.py   (http://127.0.0.1:8050)
"""

import dash_ag_grid as dag  # noqa: F401
import plotly.express as px  # noqa: F401
from dash import Dash, Input, Output, callback, dcc, html  # noqa: F401

from data import familles, load_coups, load_data  # noqa: F401

app = Dash(__name__, title="Mes parties d'échecs")
server = app.server  # Dash tourne sur Flask

app.layout = html.Div(
    [
        html.H2("Quelles ouvertures me coûtent des points ? Cliquez une barre"),
        # TODO 1. un dcc.Slider(30, 60, 10, value=30, id="n-min") et un dcc.Graph(id="familles")
        # TODO 2. un dag.AgGrid(id="parties"), une ligne sélectionnable d'un clic :
        #         dashGridOptions={"rowSelection": {"mode": "singleRow", "enableClickSelection": True}}
        # TODO 3. un dag.AgGrid(id="coups")
    ]
)

# TODO 4. callback : value de "n-min" -> figure de "familles" (px.bar de familles(df, n_min), la pire en haut).
#         Nommez-le autrement que familles (maj_familles par exemple) : sinon il masque la fonction de data.py
# TODO 5. callback : clickData de "familles" -> rowData de "parties" (les parties de cette famille)
# TODO 6. callback : selectedRows de "parties" -> rowData de "coups" (les coups jugés de cette partie)

if __name__ == "__main__":
    # debug=True : bouton « Callbacks » en bas à droite, le graphe des callbacks
    app.run(debug=False, port=8050)
