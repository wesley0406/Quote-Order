import sqlite3
import cx_Oracle
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class NN_SCREW_WATER_LEVEL :
    DB_CONFIG = {
        "host": "192.168.1.242",
        "port": 1526,
        "service_name": "sperpdb",
        "user": "spselect",
        "password": "select"
    }
    def __init__(self) :
        #self.DF_ALL_ORDER = TT.FETCH_DATA()
        self.ORDER_NUM = ""
        self.NN_TABLE = None
        self.length_mapping = {
            "01200" : "1-1/4",
            "01500" : "1-5/8",
            "02200" : "2-1/4" 
            }
        self._initialize_data()
        self.Prepare_Data()
        self.SPLIT_ORDER_AND_STOCK()


    def _get_db_connection(self):
        #Create database connection
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
        """Fetch order from database"""
        query = f"SELECT * FROM ssl_cst_orde_d"
        df = pd.read_sql_query(query, connection)

        df3 = pd.read_sql_query("SELECT SC_NO, CST_REFE_NO FROM  \
                        V_SCH0200Q_ORD WHERE ORD_CST_NO = 'D09200'", connection)
        df3 = df3.drop_duplicates(subset=["SC_NO"])

        return df.merge(df3, on = "SC_NO")

    def _initialize_data(self):
        """Initialize package weights and order data from database"""
        with self._get_db_connection() as connect:
            self.ALL_ORDER =self._fetch_order(connect)

        self.NN_TABLE  = self.ALL_ORDER.loc[
                (self.ALL_ORDER["CST_PART_NO"].str.contains("EB", na=False)) & # select the cement board order
                (self.ALL_ORDER["END_CODE"] != "D") # remove the delete item
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

        self.NN_FILTER = self.NN_FILTER[self.NN_FILTER["VEN_DLV_DATE"] >= "2025-02-23"]  # 依第一張庫存單開始計算庫存

    def SPLIT_ORDER_AND_STOCK(self):
        # Orders that contain "庫存單" (Inventory)
        inventory_table = self.NN_FILTER[self.NN_FILTER["CST_REFE_NO"].str.contains("庫存單", na=False)].copy()

        # Orders that do NOT contain "庫存單" (Regular Orders)
        order_table = self.NN_FILTER[~self.NN_FILTER["CST_REFE_NO"].str.contains("庫存單", na=False)].copy()
        order_table = order_table[order_table["VEN_DLV_DATE"] >= "2025-04-06"] 

        # calculate the moving average of each size
        grouped = self.MVA_TABLE.groupby(["SC_NO", "PDC_3"]).agg({"ORDER_QTY" : "sum"}).reset_index()


        # insure the time style
        inventory_table["VEN_DLV_DATE"] = pd.to_datetime(inventory_table["VEN_DLV_DATE"])
        order_table["VEN_DLV_DATE"] = pd.to_datetime(order_table["VEN_DLV_DATE"])

        # List of screw lengths
        screw_lengths = ["1-1/4", "1-5/8", "2-1/4"]

        # Create an empty list to store data
        all_data = []

        # Loop through each screw length and process data
        for length in screw_lengths:
            # Filter inventory and order data for the given length
            inv_filtered = inventory_table[inventory_table["PDC_3"] == length]
            ord_filtered = order_table[order_table["PDC_3"] == length]
            
            # Aggregate inventory and orders by date
            inventory_sum = inv_filtered.groupby("VEN_DLV_DATE").agg({"ORDER_QTY": "sum", "SC_NO": lambda x: ', '.join(x.unique())}).reset_index()
            inventory_sum.rename(columns={"ORDER_QTY": "Inventory_QTY"}, inplace=True)
            
            order_sum = ord_filtered.groupby("VEN_DLV_DATE").agg({"ORDER_QTY": "sum", "SC_NO": lambda x: ', '.join(x.unique())}).reset_index()
            order_sum.rename(columns={"ORDER_QTY": "Order_QTY"}, inplace=True)

            # Merge inventory and order data
            inventory_tracking = pd.merge(inventory_sum, order_sum, on="VEN_DLV_DATE", how="outer").fillna(0)
            
            # Merge the columns SC_NO_x and SC_NO_y into one column SC_NO
            inventory_tracking["SC_NO"] = inventory_tracking.apply(
            lambda row: row["SC_NO_x"] if row["SC_NO_x"] != 0 else row["SC_NO_y"], axis=1
            )

            # Drop the old SC_NO_x and SC_NO_y columns
            inventory_tracking.drop(columns=["SC_NO_x", "SC_NO_y"], inplace=True)
            
            # Sort by date for cumulative calculations
            inventory_tracking = inventory_tracking.sort_values(by="VEN_DLV_DATE")
            
            # Calculate cumulative inventory balance
            inventory_tracking["Balance"] = inventory_tracking["Inventory_QTY"].cumsum() - inventory_tracking["Order_QTY"].cumsum()
            
            # Add PDC_3 (screw length) as a column
            inventory_tracking["PDC_3"] = length
            
            # Append processed data
            all_data.append(inventory_tracking)

        # Combine all lengths into one DataFrame
        Drawing_data = pd.concat(all_data, ignore_index=True)
        Drawing_data.to_excel("水泥板螺絲庫存資料.xlsx")       # 輸出excel檔案供各部門確認

        return Drawing_data, grouped

    # draw chart
    def DRAW_CHART(self):
        # retain the dataframe
        CLEAN_FR_CHART, MVA = self.SPLIT_ORDER_AND_STOCK()
        mean_per_size = MVA.groupby("PDC_3")["ORDER_QTY"].mean()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Get the unique screw types
        screw_types = CLEAN_FR_CHART["PDC_3"].unique()

        # draw first 2 line (bigger quantity)
        for screw in screw_types[:2]:
            df_subset = CLEAN_FR_CHART[CLEAN_FR_CHART["PDC_3"] == screw]
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
                    hoverinfo="text"
                ),
                secondary_y=False
            )

        if len(screw_types) > 2:
            screw = screw_types[2]
            df_subset = CLEAN_FR_CHART[CLEAN_FR_CHART["PDC_3"] == screw]
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
                    line=dict(dash="dash", color="firebrick")
                ),
                secondary_y=True
            )

        # customizes layout
        fig.update_layout(
            title = "Inventory Balance Over Time",
            title_x = 0.5,
            title_y = 1,
            title_font = dict(size = 36, family = "Gravitas One", color = "darkblue"),
            paper_bgcolor = "bisque",
            plot_bgcolor = "seashell",
            legend = dict(
                orientation = "h",      # Horizontal layout
                yanchor = "bottom",
                y = 1.1,               # Slightly above the plot area
                xanchor = "center",
                x = 0.5,
                itemwidth = 100 ,
                )
        )
        fig.update_xaxes(gridcolor='rgba(139, 69, 19, 0.2)')  # X-axis gridline color
        fig.update_yaxes(gridcolor='rgba(139, 69, 19, 0.2)')   # Y-axis gridline color

        fig.add_annotation(
            text = "< Average Quantity per Order ({}) > <br> 1-1/4 : {:.2f}M     1-5/8 : {:.2f}M     2-1/4 : {:.2f}M".format(
                MVA["SC_NO"].nunique(),
                mean_per_size.get("1-1/4", 0),
                mean_per_size.get("1-5/8", 0),
                mean_per_size.get("2-1/4", 0)),
            xref = "paper", yref="paper",
            x = 0.5, y = -0.2,  # below the plot
            showarrow = False,
            font = dict(size = 20, color = "black")
        )

        return fig

if __name__ == "__main__":
    bot = NN_SCREW_WATER_LEVEL()
    ff = bot.DRAW_CHART()
    ff.show()






