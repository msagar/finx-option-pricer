import math
from typing import Dict, List

from dash import Dash, dash_table, dcc, html
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State

from dash_apps.utils import calc_min_max_within_strikes
from finx_option_pricer.option_plot import OptionsPlot
from finx_option_pricer.option_structures import gen_combo


app = Dash(__name__)

column_names = ['Active', 'Strike', 'Option_Type', 'DTE', 'IVfront', 'Quantity', 'Price', 'Value']

option_rows = [
    {"active": 1, "strike": 90, "option_type": "c", "dte": 80, "ivfront": 0.5, "quantity": 1},
    {"active": 1, "strike": 90.5, "option_type": "p", "dte": 21, "ivfront": 0.5, "quantity": 1},
    {"active": 1, "strike": 85, "option_type": "c", "dte": 4, "ivfront": 0.5, "quantity": -1},
    {"active": 1, "strike": 87, "option_type": "p", "dte": 4, "ivfront": 0.5, "quantity": -1},
]

app.layout = html.Div([
    html.H1(children="Generic Combo Position"),

    html.H3(children="Option Legs"),
    dash_table.DataTable(
        id='adding-rows-table',
        columns=[{
            'name': name,
            'id': f'{name.lower()}',
            'deletable': False,
            'renamable': False
        } for name in column_names],
        data=option_rows,
        editable=True,
        row_deletable=True
    ),

    html.Button('Add Row', id='editing-rows-button', n_clicks=0),

    html.H3(children="Inputs"),

    html.Label("Spot price (S) ---- "),
    dcc.Input(id="id_input_spot_price", value=80, debounce=True, type="number", min=0),
    html.Br(),

    html.Label("Spot range (SR) -- "),
    dcc.Input(id="id_input_spot_range", value=100, debounce=True, type="number", min=0),
    html.Br(),

    html.Label("Increment Days -- "),
    dcc.Input(id="id_input_increment_days", value=1, debounce=True, type="number", min=1, max=300),
    html.Br(),

    html.Label("Increment Step ---- "),
    dcc.Input(id="id_input_increment_days_step", value=1, debounce=True, type="number", min=1, max=30, step=1),
    html.Br(),

    html.Label("Vix Percent ------- "),
    dcc.Input(id="id_input_vix_percent", value=0.24, debounce=True, type="number", step=0.01),
    html.Br(),

    html.Label("Vix Std ---------- "),
    dcc.Input(id="id_input_vix_std", value=1.0, debounce=True, type="number", step=0.1),
    html.Br(),

    html.Label("Vix Days -------- "),
    dcc.Input(id="id_input_vix_days", value=10, debounce=True, type="number", step=1),
    html.Br(),

    html.Br(),

    dcc.Graph(id="graph-pnl"),
])


def _is_active(value) -> bool:
    return value != '' and int(value) == 1


@app.callback(
    Output('adding-rows-table', 'data'),
    Input('editing-rows-button', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('adding-rows-table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@app.callback(
    Output('graph-pnl', 'figure'),
    Input('adding-rows-table', 'data'),
    Input('id_input_spot_price', 'value'),
    Input('id_input_increment_days', 'value'),
    Input('id_input_spot_range', 'value'),
    Input('id_input_increment_days_step', 'value'),
    Input('id_input_vix_percent', 'value'),
    Input('id_input_vix_std', 'value'),
    Input('id_input_vix_days', 'value'),
)
def display_output(
    rows: List[Dict],
    spot_price: float,
    increment_days: int,
    spot_range: float,
    increment_days_step: int,
    vix_percent: float,
    vix_std: float,
    vix_days: int,
):

    input_list = []
    dtes = []

    for row in rows:
        if _is_active(row["active"]):
            dtes.append(int(row["dte"]))
            wanted_keys = ["strike", "option_type", "dte", "ivfront", "option_type", "quantity"]
            option_input = dict((k, row[k]) for k in wanted_keys if k in row)
            input_list.append(option_input)

    option_positions = gen_combo(spot_price=spot_price, input_list=input_list)
    strike_interval = 1.0
    spot_range: list[float, float] = [spot_price-spot_range/2, spot_price+spot_range/2]

    op_plot = OptionsPlot(
        option_positions=option_positions,
        strike_interval=strike_interval,
        spot_range=spot_range)

    df = op_plot.gen_value_df_timeincrementing(increment_days,
        step=increment_days_step,
        value_relative=True)

    df.set_index("strikes", inplace=True)

    # set time incrementing columns
    df_columns = [f"t{i*increment_days_step}" for i, _ in enumerate(df.columns)]
    df_columns[-1] = "tf"
    df.columns = df_columns

    gdf = df.reset_index().melt(id_vars=["strikes"])

    # figure - add option pnl wrt time
    fig = px.line(gdf, x="strikes", y="value", color="variable")

    # figure - add spot price
    fig.add_vline(x=spot_price, line_width=1, line_dash="dash", line_color="black")

    # figure - add strikes
    for strike in [float(x['strike']) for x in input_list]:
        fig.add_vline(x=strike, line_width=1, line_dash="dash", line_color="red")

    move_percent = vix_std * vix_percent * math.sqrt(vix_days / 252.0)
    move_underlying = spot_price * move_percent
    upside, downside = spot_price + move_underlying, spot_price - move_underlying

    fig.add_vrect(
        x0=downside,
        x1=upside,
        annotation_text=f"{vix_std}std",
        annotation_position="top left",
        fillcolor="green",
        opacity=0.1,
        line_width=2)

    # fig.add_vline(x=upside, line_width=1, line_dash="dash", line_color="green")
    # fig.add_vline(x=downside, line_width=1, line_dash="dash", line_color="green")

    # x = calc_min_max_within_strikes(df, downside, upside)
    # fig.add_hline(y=x["min"])
    # fig.add_hline(y=x["max"])

    # # figure - add initial cost
    # initial_cost = df.loc[spot_price]["t0"]
    # fig.add_hline(y=initial_cost, line_width=1, line_color="orange")


    return fig



if __name__ == '__main__':
    app.run_server(debug=True)