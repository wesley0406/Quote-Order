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
    SC_CODE = []  # Change to list to store multiple SC numbers
    
    for idx, item in enumerate(df_quote["PRODUCT_CODE"]):
        # Clean up product codes
        df_order["CLEANED_CST_PART_NO"] = df_order["CST_PART_NO"].str.replace(' #', '').str.replace('CFS/', '')
        
        # Use cleaned codes for comparison
        SINGLE_ITEM_BOARD = df_order.loc[df_order["CLEANED_CST_PART_NO"] == item].copy()
        
        if SINGLE_ITEM_BOARD.shape[0] > 0:
            # Convert quote date to datetime if it's not already
            quote_date = pd.to_datetime(df_quote.loc[0, "QUOTE_DATE"])

            SINGLE_ITEM_BOARD["CREA_DATE"] = pd.to_datetime(SINGLE_ITEM_BOARD["CREA_DATE"])
            
            SINGLE_ITEM_BOARD["TIME_DIFF"] = (SINGLE_ITEM_BOARD["CREA_DATE"] - quote_date).dt.days

            # Only accept orders that came after the quotation date
            valid_orders = SINGLE_ITEM_BOARD.loc[
                (SINGLE_ITEM_BOARD["TIME_DIFF"] > 0) &  # Changed from >= to >
                (SINGLE_ITEM_BOARD["TIME_DIFF"] <= 25)
            ]

            if valid_orders.shape[0] > 0:
                # Group by product to combine quantities from multiple orders
                grouped_orders = valid_orders.groupby("CST_PART_NO").agg({
                    "ORDER_QTY": "sum",
                    "ORDER_WEIG": "sum",
                    "SC_NO": lambda x: ", ".join(sorted(set(x)))  # Combine SC numbers
                }).reset_index()
                
                # Update the quote dataframe with combined quantities
                df_quote.at[idx, "ORDER_QTY"] = grouped_orders["ORDER_QTY"].sum()
                df_quote.at[idx, "ORDER_WEIG"] = grouped_orders["ORDER_WEIG"].sum()
                
                # Add all SC numbers to the list
                SC_CODE.extend(grouped_orders["SC_NO"].iloc[0].split(", "))
                ORDER_WEIGHT += grouped_orders["ORDER_WEIG"].sum()

    # Calculate acceptance rates
    total_items = len(df_quote)
    items_with_orders = len(df_quote[df_quote["ORDER_QTY"] > 0])
    ORDER_ACCPET_RATE_I = items_with_orders / total_items if total_items > 0 else 0
    
    total_weight = df_quote["WEIGHT"].sum()
    ORDER_ACCPET_RATE_W = ORDER_WEIGHT / total_weight if total_weight > 0 else 0
    
    # Join SC numbers with commas and remove duplicates
    SC_CODE = ", ".join(sorted(set(SC_CODE))) if SC_CODE else None

    # insure the PRODUCT NAME will be string
    df_quote["PRODUCT_CODE"] = df_quote["PRODUCT_CODE"] + "_"

    return ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I, SC_CODE, ORDER_WEIGHT, df_quote
    #return df_quote

def SEARCH_THROUGH_ITEM(item_number) :
    with sqlite3.connect(DATABASE) as connection :
        cursor = connection.cursor()
        query = f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE PRODUCT_CODE = '{item_number}'"
        df = pd.read_sql_query(query, connection)
    return df




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
                "DELETE FROM PRODUCT_ADDRESS_SUMMARY WHERE FILE_ADDRESS = ?", (file_path,)
            )
            cursor.execute(
                "DELETE FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_ADDRESS = ?",(file_path,)
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




def SINGLE_ITEM_RECORD_V2(df_quote, RAW_ORDER):
    # Input validation
    if df_quote is None or df_quote.empty:
        raise ValueError("Quote dataframe is empty")
        exit()
        

    # Initialize quote dataframe columns
    df_quote["CREA_DATE"] = None
    df_quote["ORDER_QTY"] = 0
    df_quote["ORDER_WEIG"] = 0
    df_quote["SC_CODE"] = None
    df_quote["ORDER_PRICE"] = None
    df_quote["Paired_Status"] = "Unpaired"

    # Clean up RAW_ORDER data
    RAW_ORDER["CLEANED_CST_PART_NO"] = RAW_ORDER["CST_PART_NO"].str.replace(' #', '').str.replace('CFS/', '')
    
    # Filter orders for the specific product code
    product_code = df_quote.loc[0, "PRODUCT_CODE"]
    df_order = RAW_ORDER[RAW_ORDER["CLEANED_CST_PART_NO"] == product_code].copy()
    df_order["CREA_DATE"] = pd.to_datetime(df_order["CREA_DATE"]).dt.date

    if not df_order.empty:
        # Assuming 'ORDER_NO' is the column for order number and 'QUANTITY' is the column for quantity
        df_order = df_order.groupby(['SC_NO', 'CLEANED_CST_PART_NO', 'CREA_DATE', "PRICE"])['ORDER_QTY'].sum().reset_index()
        df_order.to_excel("group_test.xlsx")
    

    # Final processing
    df_quote["QUANTITY"] = df_quote["QUANTITY"].replace(["-", 0], 100).fillna(100)  # 
    df_quote['QUOTE_DATE'] = pd.to_datetime(df_quote['QUOTE_DATE'], format='%Y%m%d')
    df_unique = df_quote.drop_duplicates(subset='QUOTE_DATE')

    # check if the order is empty
    if df_order.empty:
        print(f"No orders found for product code: {product_code}")
        return df_quote.sort_values(by="QUOTE_DATE", ascending=True), df_order

    return df_unique.sort_values(by="QUOTE_DATE", ascending=True), df_order

def test_single_item_record():
    a = FETCH_DATA()
    #a.to_excel("ALL_ORDER.xlsx")
    b = SEARCH_THROUGH_ITEM("0297134")
    quote_data, order_data = SINGLE_ITEM_RECORD_V2(b, a)
    print("\nOrder Status:")
    print(quote_data[["PRODUCT_CODE", "Paired_Status", "QUOTE_DATE"]])
    print(order_data[["CREA_DATE", "ORDER_QTY", "ORDER_WEIG", "SC_NO", "PRICE"]])
    return quote_data

if __name__ == "__main__":
    test_single_item_record()
    # ORDER = FETCH_DATA()
    # QUOTE = SEARCH_THROUGH_RFQ(6000120044)
    # ORDER_ACCPET_RATE_W, ORDER_ACCPET_RATE_I, SC_CODE, ORDER_WEIGHT, result = CONCAT_QUOTE_ORDER(QUOTE, ORDER)
    # result.columns = result.columns.str.strip() 
    # print(result)
    # print(result['PRODUCT_CODE'].dtype)
