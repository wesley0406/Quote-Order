import pandas as pd 
import os 
import re 
import time
from datetime import datetime
import sqlite3
import QUOTATION_ANALYZE_API as QA 

DB_address =  r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"
root_dir = r"C:\Users\wesley\Desktop\workboard\Verifying_File"
all_file = os.listdir(root_dir)
whole_address = [os.path.join(root_dir, i) for i in all_file]

PRODUCT_INFO, DATA_SUM, D1, D2, VER = QA.READ_FILE(whole_address[0])

VERIFTING_TABLE = DATA_SUM.loc[:, ["客戶代號", "M/盒", "USD/M\n(報價)"]]

def FIND_LAST_PRICES(item_codes):
    # Use a parameterized query to fetch all relevant items at once
    query = '''
    SELECT PRODUCT_CODE, M_BOX, TOTAL_PRICE_M, QUOTE_DATE, WIRE_PRICE, PROFIT_RATE, EXCHANGE_RATE, BOX_TYPE
    FROM CUSTOMER_PRODUCT_SUMMARY 
    WHERE PRODUCT_CODE IN ({})
    ORDER BY PRODUCT_CODE, QUOTE_DATE DESC, SERIAL_NUMBER DESC
    '''
    query = query.format(','.join('?' * len(item_codes)))
    df = pd.read_sql_query(query, DatabaseInst.conn, params=item_codes)

    # Keep only the first occurrence of each PRODUCT_CODE (most recent record)
    df = df.groupby('PRODUCT_CODE').first().reset_index()
    return df

def CREATE_HISTORY_TABLE(THE_ITEMS, CURRENCY_COLNAME):
    item_codes = THE_ITEMS["客戶代號"].unique().tolist()
    last_prices_df = FIND_LAST_PRICES(item_codes)
    
    for item_code in item_codes:
        last_price_table = last_prices_df[last_prices_df["PRODUCT_CODE"] == item_code]
        
        if not last_price_table.empty:
            last_price = last_price_table.iloc[0]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_PRICE"] = last_price["TOTAL_PRICE_M"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_PRICE_DATE"] = last_price["QUOTE_DATE"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_M_CTN"] = last_price["M_BOX"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_WIRE"] = last_price["WIRE_PRICE"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_PROFIT"] = last_price["PROFIT_RATE"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_EXCHANGE_RATE"] = last_price["EXCHANGE_RATE"]
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "BOX_TYPE"] = last_price["BOX_TYPE"]
            
            if last_price["M_BOX"] == THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "M/盒"].values[0]:
                THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "DIFFERENCE"] = \
                (THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, CURRENCY_COLNAME].values[0] - last_price["TOTAL_PRICE_M"]) / last_price["TOTAL_PRICE_M"]
        else:
            THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item_code, "LAST_PRICE"] = None
            print(f"{item_code}未報價過")
    
    FILLED_ITEM_DF = THE_ITEMS.fillna('')
   # print(FILLED_ITEM_DF)
    return FILLED_ITEM_DF




