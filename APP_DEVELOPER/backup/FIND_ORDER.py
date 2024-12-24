import cx_Oracle
import pandas as pd 
import sqlite3
import time 

DATABASE = r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"

def FETCH_DATA():
    # Define connection details
    dsn = cx_Oracle.makedsn(
        host = "192.168.1.242",      # Replace with your host IP or domain
        port = 1526,                # Replace with your port
        service_name = "sperpdb"  # Replace with your service name
    )

    # Establish the connection
    connection = cx_Oracle.connect(
        user = "spselect",         # Replace with your username
        password = "select",     # Replace with your password
        dsn = dsn
    )
    cursor = connection.cursor()
    TARGET_COLUMN = ["SC_NO",   # 公司SC號碼
                "KIND_NO",     # 訂單項次
                "CST_PART_NO", # 產品代號
                "PDC_1",       # 生產圖號
                "PDC_2",       # 螺絲規格-1
                "PDC_3",       # 螺絲規格-2
                "PDC_4",       # 螺絲種類
                "PDC_5",       # 變異碼(串華司 鏈帶 頭噴....)
                "MARK_NO",     # 頭記
                "HT_NO",       # 熱處理代號
                "FIN_NO",      # 表面處理代號
                "SALT_SPRAY",  # 鹽測小時數
                "DLV_DATE",    # 訂單交期
                "VEN_DLV_DATE",# 生管交期
                "QTY_PER_CTN", # 每箱數量
                "KEGS",        # 訂單箱數
                "ORDER_QTY1",  # 訂單量(自訂義)
                "ORDER_QTY",   # 訂單量(M)
                "ORDER_WEIG",  # 訂單項次公斤總重
                "PRICE",       # 訂單單價(/M)
                "ORDER_AMT",   # 訂單項次總價
                "PLT_QTY",     # 棧板數
                "COST_PRICE",  # 成本單價(NTD/M)
                "COST_AMT",    # 項次總成本
                "WIR_KIND",    # 線材總類(1022, 1006, 10B21)
                "PDC_1000_WT", # 單重
                "DRAW_NO",     # 圖號
                "SAMPLE_TYPE", # 是否需要樣品
                "SAMPLE_QTY",  # 客戶樣品支數
                "SAMPLE_DLV_DATE",  # 樣品交期
                "CREA_DATE",    # 訂單日期
                "CST_JOB_NO"    # 指定批號
                 ]
    query = f"SELECT {', '.join(TARGET_COLUMN)} FROM ssl_cst_orde_d"
    df = pd.read_sql_query(query, connection)
    df2 = pd.read_sql_query("SELECT SC_NO, ORD_CST_NO FROM ssl_cst_orde_m", connection)
    connection.close()
    return df2.merge(df, on = "SC_NO") 

# find the quotation through RFQ
def SEARCH_THROUGH_RFQ(quote_number):
    with sqlite3.connect(DATABASE) as connection :
        cursor = connection.cursor()
        query = f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_NUMBER = '{quote_number}'"
        df = pd.read_sql_query(query, connection)
    return df

def CONCAT_QUOTE_ORDER(df_quote, df_order) :

    # initiate the index 
    df_quote["CREA_DATE"] = None
    df_quote["ORDER_QTY"] = None
    df_quote["ORDER_WEIG"] = None
    index = 0
    ORDER_WEIGHT = 0 
    SC_CODE = None

    for item in df_quote["PRODUCT_CODE"] :
        SINGLE_ITEM_BOARD = df_order.loc[df_order["CST_PART_NO"] == item].copy()  # find the item through item code
        if SINGLE_ITEM_BOARD.shape[0] > 0 :                                # if there is item in the order , use below function to select
            SINGLE_ITEM_BOARD["TIME_DIFF"] = (SINGLE_ITEM_BOARD["CREA_DATE"] - pd.to_datetime(df_quote.loc[0, "QUOTE_DATE"])).dt.days
            valid_order = SINGLE_ITEM_BOARD.loc[(SINGLE_ITEM_BOARD["TIME_DIFF"] >= 0) &    # use 15 days to find relevent
                                                 (SINGLE_ITEM_BOARD["TIME_DIFF"] <= 15)]
            if valid_order.shape[0] > 0 :                                                  # if there is a order within 15 days then add them to the quote board
                closest_order = valid_order.loc[valid_order["TIME_DIFF"].idxmin()]          
                df_quote.at[index, "CREA_DATE"] = closest_order["CREA_DATE"]
                df_quote.at[index, "ORDER_QTY"] = closest_order["ORDER_QTY"]
                df_quote.at[index, "ORDER_WEIG"] = closest_order["ORDER_WEIG"]
                SC_CODE = closest_order["SC_NO"]
        index += 1
    ORDER_ACCPET_RATE_W = df_quote["ORDER_WEIG"].sum()/df_quote["WEIGHT"].sum()            # 重量接單率
    ORDER_ACCPET_RATE_I = df_quote["ORDER_WEIG"].notna().sum()/len(df_quote)               # 項次接單率
    ORDER_WEIGHT = df_quote["ORDER_WEIG"].sum()
    return ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I  ,SC_CODE , ORDER_WEIGHT, df_quote

def SEARCH_THROUGH_ITEM(item_number) :
    with sqlite3.connect(DATABASE) as connection :
        cursor = connection.cursor()
        query = f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE PRODUCT_CODE = '{item_number}'"
        df = pd.read_sql_query(query, connection)
    return df

def SINGLE_ITEM_RECORD(df_quote, df_order) :
    df_quote["CREA_DATE"] = None
    df_quote["ORDER_QTY"] = 0
    df_quote["ORDER_WEIG"] = 0
    df_quote["SC_CODE"] = None
    index = 0

    for item in df_quote["PRODUCT_CODE"] :
        SINGLE_ITEM_BOARD = df_order.loc[df_order["CST_PART_NO"] == item].copy()  # find the item through item code
        if SINGLE_ITEM_BOARD.shape[0] > 0 :                                # if there is item in the order , use below function to select
            SINGLE_ITEM_BOARD["TIME_DIFF"] = (SINGLE_ITEM_BOARD["CREA_DATE"] - pd.to_datetime(df_quote.loc[index, "QUOTE_DATE"])).dt.days
            valid_order = SINGLE_ITEM_BOARD.loc[(SINGLE_ITEM_BOARD["TIME_DIFF"] >= 0) &    # use 15 days to find relevent
                                                 (SINGLE_ITEM_BOARD["TIME_DIFF"] <= 25)]
            if valid_order.shape[0] > 0 :                                                  # if there is a order within 15 days then add them to the quote board
                closest_order = valid_order.loc[valid_order["TIME_DIFF"].idxmin()]          
                df_quote.at[index, "CREA_DATE"] = closest_order["CREA_DATE"]
                df_quote.at[index, "ORDER_QTY"] = closest_order["ORDER_QTY"]
                df_quote.at[index, "ORDER_WEIG"] = closest_order["ORDER_WEIG"]
                df_quote.at[index, "SC_CODE"]= closest_order["SC_NO"]
        index += 1
    df_quote["QUANTITY"] = pd.to_numeric(df_quote["QUANTITY"], errors="coerce").fillna(0)
    # df_quote["ORDER_RATE"] = df_quote["ORDER_QTY"]/df_quote["QUANTITY"]*100
    # df_quote["ORDER_RATE"] = df_quote["ORDER_RATE"].map("{:.2f}%".format)
    df_quote['QUOTE_DATE'] = pd.to_datetime(df_quote['QUOTE_DATE'], format='%Y%m%d')

    df_unique = df_quote.drop_duplicates(subset='QUOTE_DATE')            # remvove the duplicate quote date
    return df_unique.sort_values(by="QUOTE_DATE", ascending=True)










