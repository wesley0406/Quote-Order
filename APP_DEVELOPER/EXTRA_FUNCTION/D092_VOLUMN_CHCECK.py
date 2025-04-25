import sqlite3
import cx_Oracle
import pandas as pd

class NN_CHECKVOLUMN :
    PALLET_WEIGHT = 20  # Define constant for pallet weight
    DB_CONFIG = {
        "host": "192.168.1.242",
        "port": 1526,
        "service_name": "sperpdb",
        "user": "spselect",
        "password": "select"
    }
    def __init__(self) :
        self.ORDER_NUM = ""
        self.PCK_WEI_DF = None
        self.ORDER_WEI_SUM  = 0
        self.DOUBLE_PALLETS = 0
        self.TRIPLE_PALLETS = 0
        self.TOTAL_WEIGHT = 0

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
    def _fetch_package_weights(self, connection):
        """Fetch package weights from database"""
        query = "SELECT PMT_NO, PCK_NAME, CTN_WT FROM sbs_pck_mate WHERE CST_NO = 'D09200'"
        return pd.read_sql_query(query, connection)

    def _fetch_order_data(self, connection):
        """Fetch order data from database"""
        query = f"SELECT * FROM ssl_cst_orde_d WHERE SC_NO = '{self.ORDER_NUM}'"
        return pd.read_sql_query(query, connection)
    
    def _initialize_data(self):
        """Initialize package weights and order data from database"""
        with self._get_db_connection() as connection:
            self.PCK_WEI_DF = self._fetch_package_weights(connection)
            self.order_df = self._fetch_order_data(connection)


    def ORDER_WEI_SUMMERIZED(self):

        # 2. Select relevant columns with descriptive names
        required_columns = {
            "CST_PART_NO": "item_code",
            "PMT_NO": "carton_code",
            "SML_PMT_NO": "inner_box_code",
            "SMALL_PACK_QTY": "qty_per_inner",
            "KEGS": "carton_qty",
            "BOXES": "inner_box_qty",
            "PLT_QTY": "pallet_qty",
            "ORDER_WEIG": "screw_weight"
        }
        weight_df = self.order_df[list(required_columns.keys())].copy()
        weight_df = weight_df.rename(columns=required_columns)
        weight_df = weight_df.fillna(0)

        # 3. Calculate package weights
        package_weights = self.PCK_WEI_DF.set_index("PMT_NO")["CTN_WT"]
        weight_df["carton_weight"] = weight_df["carton_code"].map(package_weights)
        weight_df["inner_box_weight"] = weight_df["inner_box_code"].map(package_weights)
        weight_df = weight_df.fillna(0)
        # 4. Calculate total packaging weight
        
        weight_df["total_package_weight"] = (
            (weight_df["inner_box_qty"] * weight_df["inner_box_weight"]) +
            (weight_df["carton_qty"] * weight_df["carton_weight"])
        ) 
        # 5. Calculate final weight including pallets , screws and package
        self.TOTAL_WEIGHT = (
            weight_df["total_package_weight"].sum() +
            weight_df["pallet_qty"].sum() * self.PALLET_WEIGHT +
            weight_df["screw_weight"].sum()
        )
        # 6. Calculate pallet quantities for different scenarios
        self.TRIPLE_PALLETS = weight_df.loc[weight_df["inner_box_qty"] == 0, "pallet_qty"].sum()
        self.DOUBLE_PALLETS = weight_df.loc[weight_df["inner_box_qty"] > 1, "pallet_qty"].sum()
        return weight_df

# if __name__ == "__main__":
#     bot = NN_CHECKVOLUMN()
#     total_df = bot.ORDER_WEI_SUMMERIZED()



