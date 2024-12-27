import sys
import os
import importlib.util

# Update the path to the correct location
UDF_DIR = r"C:\Users\wesley\Desktop\workboard\QUOTE_CENTER"
sys.path.append(UDF_DIR)

# Get the full path to UPDATE_DB_FUNC.py
udf_path = os.path.join(UDF_DIR, "UPDATE_DB_FUNC.py")

try:
    # Load the module
    spec = importlib.util.spec_from_file_location("UPDATE_DB_FUNC", udf_path)
    UDF = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(UDF)
except Exception as e:
    print(f"Error loading UPDATE_DB_FUNC.py: {e}")

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
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        query = f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_NUMBER = '{quote_number}'"
        df = pd.read_sql_query(query, connection)
        
        # Check if quotation exists
        if df.empty:
            return None  # Return None instead of empty DataFrame
    return df

def CONCAT_QUOTE_ORDER(df_quote, df_order):
    # Check if quotation exists
    if df_quote is None:
        print("Warning: Quotation number does not exist")
        return None, None, None, None, None  # Return None for all values
        
    # Validate input dataframes
    if df_quote.empty:
        print("Warning: Quote dataframe is empty")
        return 0, 0, None, 0, pd.DataFrame()

    if df_order.empty:
        print("Warning: Order dataframe is empty")
        return 0, 0, None, 0, df_quote

    # Check if required columns exist
    required_columns = ["PRODUCT_CODE", "WEIGHT", "QUOTE_DATE"]
    if not all(col in df_quote.columns for col in required_columns):
        print("Warning: Missing required columns in quote dataframe")
        return 0, 0, None, 0, df_quote

    # initiate the index 
    df_quote["CREA_DATE"] = None
    df_quote["ORDER_QTY"] = None
    df_quote["ORDER_WEIG"] = None
    index = 0
    ORDER_WEIGHT = 0 
    SC_CODE = None

    for item in df_quote["PRODUCT_CODE"]:
        # Clean up order product codes as well
        df_order["CLEANED_CST_PART_NO"] = df_order["CST_PART_NO"].str.replace(' #', '').str.replace('CFS/', '')
        
        # Use cleaned codes for comparison
        SINGLE_ITEM_BOARD = df_order.loc[df_order["CLEANED_CST_PART_NO"] == item].copy()
        
        if SINGLE_ITEM_BOARD.shape[0] > 0:
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
    df_quote["QUANTITY"] = df_quote["QUANTITY"].replace(["-", 0], 1).fillna(1)             # 將成本表中沒有需求數量的向次需求量改1

    # Add error handling for weight calculations
    try:
        total_weight = df_quote["WEIGHT"].sum()
        total_order_weight = df_quote["ORDER_WEIG"].sum()
        
        # Check for zero division
        if total_weight == 0:
            ORDER_ACCPET_RATE_W = 0
        else:
            ORDER_ACCPET_RATE_W = total_order_weight / total_weight  # 重量接單率

        # Check for zero division for item rate
        total_items = len(df_quote)
        if total_items == 0:
            ORDER_ACCPET_RATE_I = 0
        else:
            ORDER_ACCPET_RATE_I = df_quote["ORDER_WEIG"].notna().sum() / total_items  # 項次接單率

        ORDER_WEIGHT = total_order_weight

    except Exception as e:
        print(f"Error in rate calculation: {e}")
        ORDER_ACCPET_RATE_W = 0
        ORDER_ACCPET_RATE_I = 0
        ORDER_WEIGHT = 0

    return ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I, SC_CODE, ORDER_WEIGHT, df_quote

def SEARCH_THROUGH_ITEM(item_number) :
    with sqlite3.connect(DATABASE) as connection :
        cursor = connection.cursor()
        query = f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE PRODUCT_CODE like '%{item_number}'"
        df = pd.read_sql_query(query, connection)
    return df

def SINGLE_ITEM_RECORD(df_quote, df_order):
    df_quote["CREA_DATE"] = None
    df_quote["ORDER_QTY"] = 0
    df_quote["ORDER_WEIG"] = 0
    df_quote["SC_CODE"] = None
    df_quote["ORDER_PRICE"] = None
    index = 0

    for item in df_quote["PRODUCT_CODE"]:
        # Clean up product codes
        cleaned_item = item.replace('#', '').replace('CFS/', '')
        # Clean up order product codes
        df_order["CLEANED_CST_PART_NO"] = df_order["CST_PART_NO"].str.replace('#', '').str.replace('CFS/', '')
        
        # Use cleaned codes for comparison
        SINGLE_ITEM_BOARD = df_order.loc[df_order["CLEANED_CST_PART_NO"] == cleaned_item].copy()
        
        if SINGLE_ITEM_BOARD.shape[0] > 0:
            # Convert CREA_DATE to date only (removing time component)
            SINGLE_ITEM_BOARD["CREA_DATE"] = pd.to_datetime(SINGLE_ITEM_BOARD["CREA_DATE"]).dt.date
            
            SINGLE_ITEM_BOARD["TIME_DIFF"] = (pd.to_datetime(SINGLE_ITEM_BOARD["CREA_DATE"]) - 
                                            pd.to_datetime(df_quote.loc[index, "QUOTE_DATE"])).dt.days
            
            valid_orders = SINGLE_ITEM_BOARD.loc[(SINGLE_ITEM_BOARD["TIME_DIFF"] >= 0) & 
                                               (SINGLE_ITEM_BOARD["TIME_DIFF"] <= 25)]
            
            if valid_orders.shape[0] > 0:
                # Group orders by date (time component already removed)
                same_date_orders = valid_orders.groupby("CREA_DATE").agg({
                    "ORDER_QTY": "sum",
                    "ORDER_WEIG": "sum",
                    "SC_NO": lambda x: ", ".join(sorted(x.unique())),
                    "PRICE": "first"
                }).reset_index()
                
                # Get the earliest date's orders
                earliest_date = same_date_orders["CREA_DATE"].min()
                combined_order = same_date_orders.loc[same_date_orders["CREA_DATE"] == earliest_date].iloc[0]

                # Update the quote dataframe
                df_quote.at[index, "CREA_DATE"] = pd.to_datetime(combined_order["CREA_DATE"])
                df_quote.at[index, "ORDER_QTY"] = combined_order["ORDER_QTY"]
                df_quote.at[index, "ORDER_WEIG"] = combined_order["ORDER_WEIG"]
                df_quote.at[index, "SC_CODE"] = combined_order["SC_NO"]
                df_quote.at[index, "ORDER_PRICE"] = combined_order["PRICE"]
        
        index += 1

    df_quote["QUANTITY"] = df_quote["QUANTITY"].replace(["-", 0], 1).fillna(1)
    df_quote['QUOTE_DATE'] = pd.to_datetime(df_quote['QUOTE_DATE'], format='%Y%m%d')
    df_unique = df_quote.drop_duplicates(subset='QUOTE_DATE')
    return df_unique.sort_values(by="QUOTE_DATE", ascending=True)


def UPDATEDB_BYFILE(file_path):
    try:
        if not file_path:
            raise ValueError("Please enter a valid file address.")

        # Verify UDF module is properly imported
        if 'UDF' not in globals():
            raise ImportError("Could not import UPDATE_DB_FUNC module. Please check the file path.")

        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()

            # Delete old data
            cursor.execute(
                "DELETE FROM PRODUCT_ADDRESS_SUMMARY WHERE FILE_ADDRESS = ?",
                (file_path,)
            )
            cursor.execute(
                "DELETE FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_ADDRESS = ?",
                (file_path,)
            )

            try:
                # Reload the data into DB
                PRODUCT_INFO, DATA_SUM, D1, D2, VER = UDF.READ_FILE(file_path)
                cursor.execute(
                    "INSERT INTO PRODUCT_ADDRESS_SUMMARY (FILE_ADDRESS) VALUES (?);",
                    (file_path,)
                )

                # Insert the data
                UDF.QUOTATION_INSERT(DATA_SUM, "CUSTOMER_PRODUCT_SUMMARY", "QUOTATION_DATABASE.db", cursor)
                
                return True

            except AttributeError as e:
                raise Exception(f"Error in UPDATE_DB_FUNC module: {str(e)}")

    except ImportError as e:
        raise Exception(f"Import error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error updating database: {str(e)}")





