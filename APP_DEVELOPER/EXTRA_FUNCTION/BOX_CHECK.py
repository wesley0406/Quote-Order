import sqlite3
import cx_Oracle
import pandas as pd

class BOX_CHECK :
    DB_CONFIG = {
        "host": "192.168.1.242",
        "port": 1526,
        "service_name": "sperpdb",
        "user": "spselect",
        "password": "select"
    }
    required_columns_ERP = [
    	"CST_PART_NO",
    	"PDC_1",
    	"DLV_DATE",
    	"PMT_NO",
    	"QTY_PER_CTN"
    ]
    	

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

    # find the same product before in the ERP and get the latest one 
    def FIND_ERP(self, ITEM_CODE):
    	query = f"SELECT {', '.join(self.required_columns_ERP)} FROM ssl_cst_orde_d WHERE CST_PART_NO = '{ITEM_CODE}' ORDER BY DLV_DATE DESC"
    	with self._get_db_connection() as connection:
    		history_data = pd.read_sql_query(query, connection)
    		history_data["QTY_PER_CTN"] = history_data["QTY_PER_CTN"]*1000
    	return history_data.iloc[0, :]
    # use the excel file to 
    def C019_preprocess(self):
    	ALL_ITEM_DF = pd.read_excel("C019_ALL_ITEM.xlsx")
    	USE_COLUMN = ALL_ITEM_DF.iloc[:, [0, 1, 9, 15, 38, 39]]
    	USE_COLUMN["每箱量"] = USE_COLUMN["每箱量"]*1000
    	USE_COLUMN["QUOTE_CODE"] = USE_COLUMN["外箱包材代號"].map(self.BOX_TYPE_REF)
    	print(USE_COLUMN)


if __name__ == "__main__":
    bot = BOX_CHECK()
    bot.C019_preprocess()
    #total_df = bot.FIND_ERP("89096.014.0060.100")