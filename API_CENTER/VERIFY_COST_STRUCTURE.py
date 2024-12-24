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

def FIND_THE_LAST_PRICE(item_code, DB):
    # Use a parameterized query to avoid SQL injection risks
    query = '''
    SELECT PRODUCT_CODE, M_BOX, TOTAL_PRICE_M , QUOTE_DATE, WIRE_PRICE, PROFIT_RATE, EXCHANGE_RATE 
    FROM CUSTOMER_PRODUCT_SUMMARY 
    WHERE PRODUCT_CODE = ? 
    ORDER BY QUOTE_DATE DESC, SERIAL_NUMBER  DESC
    LIMIT 1
    '''
    with sqlite3.connect(DB) as connect:
    	df = pd.read_sql_query(query, connect, params = (item_code,))
    return df

def CREATE_HISTORY_TABLE(THE_ITEMS):
	BASE = pd.DataFrame(columns=["PRODUCT_CODE", "M_BOX", "TOTAL_PRICE_M"])
	base_list = []

	for item in THE_ITEMS["客戶代號"]:
		last_price_table = FIND_THE_LAST_PRICE(item, DB_address)
		#核對是否報過價
		if not last_price_table.empty :
			last_price = last_price_table["TOTAL_PRICE_M"].values[0]              
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_PRICE"] = last_price                                      # 紀錄上次價格
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_PRICE_DATE"] = last_price_table["QUOTE_DATE"].values[0]   #  紀錄上次報價日期
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_M_CTN"] = last_price_table["M_BOX"].values[0]              #  紀錄上次每盒支數
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_WIRE"] = last_price_table["WIRE_PRICE"].values[0]          #  紀錄上次線材價格
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_PROFIT"] = last_price_table["PROFIT_RATE"].values[0]       #  紀錄上次利潤率
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_EXCHANGE_RATE"] = last_price_table["EXCHANGE_RATE"].values[0] #  紀錄上次匯率

			# 核對每箱支數是否確
			if last_price_table["M_BOX"].values[0] == THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "M/盒"].values[0]:
				THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "DIFFERENCE"] = (last_price - THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, THE_ITEMS.columns[3]].values[0]) / last_price  # 紀錄兩次差異
			else :
				THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_PRICE"] = "{} Mpcs/carton is wrong !!!".format(item)
				THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "DIFFERENCE"] = "No data"
				#print("{}每箱支數有誤".format(item))	
		else :
			THE_ITEMS.loc[THE_ITEMS["客戶代號"] == item, "LAST_PRICE"] = "{} Not quoted yet.".format(item)
			print("{}未報價過".format(item))
	return THE_ITEMS	




