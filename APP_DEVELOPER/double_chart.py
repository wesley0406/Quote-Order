import sqlite3
import cx_Oracle
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output

class NN_SCREW_WATER_LEVEL:
    DB_CONFIG = {
        "host": "192.168.1.242",
        "port": 1526,
        "service_name": "sperpdb",
        "user": "spselect",
        "password": "select"
    }
    
    def __init__(self):
        self.ORDER_NUM = ""
        self.NN_TABLE = None
        self.length_mapping = {
            "01200": "1-1/4",
            "01500": "1-5/8",
            "02200": "2-1/4"
        }
        self._initialize_data()
        self.Prepare_Data()
        self.SPLIT_ORDER_AND_STOCK()

    def _get_db_connection(self):
        dsn = cx_Oracle.makedsn(
            host=self.DB_CONFIG["host"],
            port=self.DB_CONFIG["port"],
            service_name=self.DB_CONFIG["service_name"]
        )
        return cx_Oracle.connect(
            user=self.DB_CONFIG["user"],
            password=self.DB_CONFIG["password"],
            dsn=dsn
        )

    def _fetch_order(self, connection):
        query = "SELECT * FROM ssl_cst_orde_d"
        df = pd.read_sql_query(query, connection)
        df3 = pd.read_sql_query("SELECT SC_NO, CST_REFE_NO FROM V_SCH0200Q_ORD WHERE ORD_CST_NO = 'D09200'", connection)
        df3 = df3.drop_duplicates(subset=["SC_NO"])
        return df.merge(df3, on="SC_NO")

    def _initialize_data(self):
        with self._get_db_connection() as connect:
            self.ALL_ORDER = self._fetch_order(connect)
        self.NN_TABLE = self.ALL_ORDER.loc[
            (self.ALL_ORDER["CST_PART_NO"].str.contains("EB", na=False)) &
            (self.ALL_ORDER["END_CODE"] != "D")
        ]

    def Prepare_Data(self):
        self.NN_FILTER = self.NN_TABLE[["SC_NO", 
            "CST_REFE_NO", 
            "CST_PART_NO", 
            "PDC_3",
            "VEN_DLV_DATE",
            "ORDER_QTY",
            "ORDER_WEIG"]].copy().sort_values(by="VEN_DLV_DATE")

        self.NN_FILTER["PDC_3"] = self.NN_FILTER["PDC_3"].map(self.length_mapping)
        self.MVA_TABLE = self.NN_FILTER[~self.NN_FILTER["CST_REFE_NO"].str.contains("庫存單", na=False)].copy()

        self.NN_FILTER = self.NN_FILTER[self.NN_FILTER["VEN_DLV_DATE"] >= "2025-02-23"]

    def SPLIT_ORDER_AND_STOCK(self):
        inventory_table = self.NN_FILTER[self.NN_FILTER["CST_REFE_NO"].str.contains("庫存單", na=False)].copy()
        order_table = self.NN_FILTER[~self.NN_FILTER["CST_REFE_NO"].str.contains("庫存單", na=False)].copy()
        order_table = order_table[order_table["VEN_DLV_DATE"] >= "2025-04-06"]
        grouped = self.MVA_TABLE.groupby(["SC_NO", "PDC_3"]).agg({"ORDER_QTY": "sum"}).reset_index()

        inventory_table["VEN_DLV_DATE"] = pd.to_datetime(inventory_table["VEN_DLV_DATE"])
        order_table["VEN_DLV_DATE"] = pd.to_datetime(order_table["VEN_DLV_DATE"])

        screw_lengths = ["1-1/4", "1-5/8", "2-1/4"]
        all_data = []

        for length in screw_lengths:
            inv_filtered = inventory_table[inventory_table["PDC_3"] == length]
            ord_filtered = order_table[order_table["PDC_3"] == length]
            inventory_sum = inv_filtered.groupby("VEN_DLV_DATE").agg({"ORDER_QTY": "sum", "SC_NO": lambda x: ', '.join(x.unique())}).reset_index()
            inventory_sum.rename(columns={"ORDER_QTY": "Inventory_QTY"}, inplace=True)
            order_sum = ord_filtered.groupby("VEN_DLV_DATE").agg({"ORDER_QTY": "sum", "SC_NO": lambda x: ', '.join(x.unique())}).reset_index()
            order_sum.rename(columns={"ORDER_QTY": "Order_QTY"}, inplace=True)

            inventory_tracking = pd.merge(inventory_sum, order_sum, on="VEN_DLV_DATE", how="outer").fillna(0)
            inventory_tracking["SC_NO"] = inventory_tracking.apply(
                lambda row: row["SC_NO_x"] if row["SC_NO_x"] != 0 else row["SC_NO_y"], axis=1
            )
            inventory_tracking.drop(columns=["SC_NO_x", "SC_NO_y"], inplace=True)
            inventory_tracking = inventory_tracking.sort_values(by="VEN_DLV_DATE")
            inventory_tracking["Balance"] = inventory_tracking["Inventory_QTY"].cumsum() - inventory_tracking["Order_QTY"].cumsum()
            inventory_tracking["PDC_3"] = length
            all_data.append(inventory_tracking)

        Drawing_data = pd.concat(all_data, ignore_index=True)
        Drawing_data.to_excel("水泥板螺絲庫存資料.xlsx")
        return Drawing_data, grouped

    def DRAW_CHART(self):
        try:
            CLEAN_FR_CHART, MVA = self.SPLIT_ORDER_AND_STOCK()
            if CLEAN_FR_CHART.empty:
                return go.Figure(
                    layout=dict(
                        title="No Data Available",
                        title_x=0.5,
                        paper_bgcolor="bisque",
                        plot_bgcolor="seashell"
                    )
                )

            mean_per_size = MVA.groupby("PDC_3")["ORDER_QTY"].mean()
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            screw_types = CLEAN_FR_CHART["PDC_3"].unique()
            dates = sorted(CLEAN_FR_CHART["VEN_DLV_DATE"].unique())

            if not dates:
                return go.Figure(
                    layout=dict(
                        title="No Valid Dates Available",
                        title_x=0.5,
                        paper_bgcolor="bisque",
                        plot_bgcolor="seashell"
                    )
                )

            # Add full traces for each screw type
            for i, screw in enumerate(screw_types):
                df_subset = CLEAN_FR_CHART[CLEAN_FR_CHART["PDC_3"] == screw]
                is_secondary = screw == "2-1/4" and len(screw_types) > 2
                fig.add_trace(
                    go.Scatter(
                        x=df_subset["VEN_DLV_DATE"],
                        y=df_subset["Balance"],
                        mode="lines+markers",
                        name=f"{screw}\u2003\u2003",
                        hovertext=(
                            "SC_NO: " + df_subset["SC_NO"].astype(str) +
                            "<br>Order_QTY: " + df_subset["Order_QTY"].astype(str) +
                            "<br>Inventory_QTY: " + df_subset["Inventory_QTY"].astype(str) +
                            "<br>Current_QTY: " + df_subset["Balance"].map("{:.2f}".format) +
                            "<br>Delivery Date: " + df_subset["VEN_DLV_DATE"].astype(str)
                        ),
                        hoverinfo="text",
                        line=dict(color="firebrick" if is_secondary else None),
                        yaxis="y2" if is_secondary else "y1"
                    ),
                    secondary_y=is_secondary
                )

            # Update layout with slider to filter by date
            fig.update_layout(
                title="Inventory Balance Over Time",
                title_x=0.5,
                title_y=1,
                title_font=dict(size=36, family="Gravitas One", color="darkblue"),
                paper_bgcolor="bisque",
                plot_bgcolor="seashell",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.1,
                    xanchor="center",
                    x=0.5,
                    itemwidth=100,
                ),
                xaxis=dict(
                    title="Delivery Date",
                    gridcolor='rgba(139, 69, 19, 0.2)',
                    range=[min(dates), max(dates)] if dates else None
                ),
                yaxis=dict(
                    title="Balance (1-1/4, 1-5/8)",
                    gridcolor='rgba(139, 69, 19, 0.2)'
                ),
                yaxis2=dict(
                    title="Balance (2-1/4)",
                    gridcolor='rgba(139, 69, 19, 0.2)',
                    overlaying="y",
                    side="right"
                ),
                sliders=[dict(
                    steps=[
                        dict(
                            method="restyle",
                            args=[
                                {
                                    "x": [
                                        CLEAN_FR_CHART[
                                            (CLEAN_FR_CHART["PDC_3"] == screw) &
                                            (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                        ]["VEN_DLV_DATE"].tolist()
                                        for screw in screw_types
                                    ],
                                    "y": [
                                        CLEAN_FR_CHART[
                                            (CLEAN_FR_CHART["PDC_3"] == screw) &
                                            (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                        ]["Balance"].tolist()
                                        for screw in screw_types
                                    ],
                                    "hovertext": [
                                        (
                                            "SC_NO: " + CLEAN_FR_CHART[
                                                (CLEAN_FR_CHART["PDC_3"] == screw) &
                                                (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                            ]["SC_NO"].astype(str) +
                                            "<br>Order_QTY: " + CLEAN_FR_CHART[
                                                (CLEAN_FR_CHART["PDC_3"] == screw) &
                                                (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                            ]["Order_QTY"].astype(str) +
                                            "<br>Inventory_QTY: " + CLEAN_FR_CHART[
                                                (CLEAN_FR_CHART["PDC_3"] == screw) &
                                                (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                            ]["Inventory_QTY"].astype(str) +
                                            "<br>Current_QTY: " + CLEAN_FR_CHART[
                                                (CLEAN_FR_CHART["PDC_3"] == screw) &
                                                (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                            ]["Balance"].map("{:.2f}".format) +
                                            "<br>Delivery Date: " + CLEAN_FR_CHART[
                                                (CLEAN_FR_CHART["PDC_3"] == screw) &
                                                (CLEAN_FR_CHART["VEN_DLV_DATE"] <= date)
                                            ]["VEN_DLV_DATE"].astype(str)
                                        ).tolist()
                                        for screw in screw_types
                                    ]
                                },
                                list(range(len(screw_types)))  # Update all traces
                            ],
                            label=str(date)[:10]
                        ) for date in dates
                    ],
                    active=len(dates),  # Start at the last date (full chart)
                    pad={"t": 55},
                    currentvalue={"prefix": "Date: ", "font": {"size": 20}}
                )]
            )

            # Add annotation for average quantities
            fig.add_annotation(
                text="< Average Quantity per Order ({}) > <br> 1-1/4 : {:.2f}M     1-5/8 : {:.2f}M     2-1/4 : {:.2f}M".format(
                    MVA["SC_NO"].nunique(),
                    mean_per_size.get("1-1/4", 0),
                    mean_per_size.get("1-5/8", 0),
                    mean_per_size.get("2-1/4", 0)),
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.2,
                showarrow=False,
                font=dict(size=20, color="black")
            )

            return fig
        except Exception as e:
            return go.Figure(
                layout=dict(
                    title=f"Error: {str(e)}",
                    title_x=0.5,
                    paper_bgcolor="bisque",
                    plot_bgcolor="seashell"
                )
            )

# Dash App
app = Dash(__name__)

bot = NN_SCREW_WATER_LEVEL()

app.layout = html.Div([
    html.H1("Cement Screw Inventory Dashboard", style={"textAlign": "center", "color": "darkblue"}),
    html.Button("Show Cement Statistic Chart", id="cement_statistic_button", n_clicks=0, 
                style={"margin": "20px auto", "display": "block", "padding": "10px 20px", "fontSize": "16px"}),
    html.Div(id="quotation-output", style={"margin": "20px"})
])

@app.callback(
    Output("quotation-output", "children"),
    Input("cement_statistic_button", "n_clicks"),
    prevent_initial_call=True
)
def Cement_Chart(n_clicks):
    fig = bot.DRAW_CHART()
    return dcc.Graph(id="main-chart", figure=fig, style={"width": "100%", "height": "700px"})

if __name__ == "__main__":
    app.run(debug=True)