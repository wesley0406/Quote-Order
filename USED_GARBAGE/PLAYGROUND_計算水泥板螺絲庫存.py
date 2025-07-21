import pandas as pd 
import sqlite3
import time , cx_Oracle, os, sys

sys.path.append(r"C:\Users\wesley\Desktop\workboard\APP_DEVELOPER\EXTRA_FUNCTION")
from CARBON_TRACK_FUNC import CO2_Calculator 

def FETCH_DATA_CARBON():
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
    query = "SELECT SHEET_NO,  PROC_DATE, TOT_WT,  AFM_VEN_NO FROM ACM_DELV_M WHERE DRIVER = '04'"    # 線材代工
    df_OEM = pd.read_sql_query(query, connection)

    query = "SELECT SALE_NO, SALE_DATE, TOT_WT, AFM_VEN_NO FROM WPC_WIR_SALE_M WHERE DRIVER = '04'" # 線材銷售
    df_WIRE_SALE = pd.read_sql_query(query, connection)

    query = "SELECT SHEET_NO, PROC_DATE FROM ASK_HD_TRAN_OS_M WHERE  DRIVER = '04' " # 加工線出貨 篩選李國忠
    FORMING_BY4 = pd.read_sql_query(query, connection)
    query = "SELECT SHEET_NO, WEIGHT, DLV_VEN_NO FROM ASK_HD_TRAN_OS_D_OEM"        # 全加工線出貨訂單
    FORMING_ALL= pd.read_sql_query(query, connection)
    FORMING_ALL = FORMING_ALL.groupby(["SHEET_NO", "DLV_VEN_NO"])["WEIGHT"].sum().reset_index()

    # mergen the forming line 
    FORMING_INDEXED = FORMING_ALL.set_index("SHEET_NO")
    FORMING_BY4["WEIGHT"] = FORMING_BY4["SHEET_NO"].map(FORMING_INDEXED["WEIGHT"])
    FORMING_BY4["DESTINATION"] = FORMING_BY4["SHEET_NO"].map(FORMING_INDEXED["DLV_VEN_NO"])

    # standardizing the column name
    df_OEM.rename(columns={"TOT_WT": "WEIGHT", "AFM_VEN_NO": "DESTINATION"}, inplace=True)
    df_WIRE_SALE.rename(columns={"SALE_NO" : "SHEET_NO","SALE_DATE" : "PROC_DATE", "TOT_WT": "WEIGHT", "AFM_VEN_NO": "DESTINATION"}, inplace=True)

    FINAL = pd.concat([df_OEM, df_WIRE_SALE, FORMING_BY4], ignore_index=True).sort_values(by = "PROC_DATE").reset_index()
    FINAL =  FINAL.groupby(["PROC_DATE", "DESTINATION"])["WEIGHT"].sum().reset_index() # 將每日同一指送地加總

    return FINAL

def SPLIT_DRIVE(MILE_TABLE):
    MILE_TABLE["PROC_DATE"] = pd.to_datetime(MILE_TABLE["PROC_DATE"])

    daily_total = MILE_TABLE.groupby(MILE_TABLE["PROC_DATE"].dt.date)["WEIGHT"].sum()

    MILE_TABLE["DRIVE"] = 1

    for date, ALL_weight in daily_total.items():
        if ALL_weight > 23500 :
            day_mask = MILE_TABLE["PROC_DATE"].dt.date == date
            sorted_df = MILE_TABLE[day_mask].sort_values(by = "WEIGHT", ascending = False).copy()

            cumulative_weight = 0
            drive_flag = 1

            for idx in sorted_df.index : 
                cumulative_weight += sorted_df.at[idx, "WEIGHT"]
                MILE_TABLE.at[idx, "DRIVE"] = drive_flag

                if cumulative_weight > 23500 and drive_flag == 1 :
                    drive_flag = 2 

    #MILE_TABLE.to_excel("split_file.xlsx")
    return MILE_TABLE

def transform_weight_reverse(group):
    """Reverse the WEIGHT column and replace each value with the cumulative sum from the bottom."""
    group = group.iloc[::-1].copy()  # Reverse the order
    group["WEIGHT"] = group["WEIGHT"].cumsum()  # Compute cumulative sum from the bottom
    group = group.iloc[::-1]  # Restore original order
    return group

def split_and_save_excel(df, output_folder="2024_CO2"):

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Convert PROC_DATE to date format (YYYY-MM-DD)
    df["PROC_DATE"] = pd.to_datetime(df["PROC_DATE"])
    
    # Filter only rows where the year is 2024
    df = df[df["PROC_DATE"].dt.year == 2024].copy()

    # Convert PROC_DATE to date format (YYYY-MM-DD)
    df["PROC_DATE"] = df["PROC_DATE"].dt.date

    # Iterate through unique (PROC_DATE, DRIVE) pairs
    for (date, drive), group in df.groupby(["PROC_DATE", "DRIVE"]):
        filename = f"{output_folder}/{date}-{drive}.xlsx"  # Generate filename

        transformed_group = transform_weight_reverse(group)
        transformed_group.rename(columns={"DESTINATION": "FACTORY_CODE", "WEIGHT": "KGS"}, inplace=True)
        transformed_group[["FACTORY_CODE", "KGS"]].to_excel(filename, index=False)
        
        print(f"Saved: {filename}")

#SUMMARY_MILE = FETCH_DATA_CARBON()
#SPLIT_DF = SPLIT_DRIVE(SUMMARY_MILE)
#split_and_save_excel(SPLIT_DF)

def CARBON_CALCULATOR() :
    TARCK_RECORD = {}
    REVIEW_CO2_EMISSION = pd.DataFrame(columns = ["ORDER_NUMBER", "DISTANCE", "CO2 TONS/KM"])

    #Define the root directory where your files are located
    root_directory = r"Z:\\跨部門\\共用資料夾\\F. 管理部\\05.碳盤查資訊與資料\\類別三\\(下游運輸) 外車司機\\2025_CARTRACK_SUMMARY\\2025_CAR_TRACK"   # please redefine your own root or file 
    #ith open(f'TRACK_LOG.txt', 'w') as log_file:  # 'w' mode clears the file
        #log_file.write("Starting new log!\n")
    CALCULATOR = CO2_Calculator()
    for root, dirs, files in os.walk(root_directory):
        n = 0 
        for i in files : 
            order, dis, co2 , track_dic = CALCULATOR.TRANS_ORDER_INTO_CO2(os.path.join(root_directory,i)) # 丟入欲計算的派車單進root_directory資料夾
            TARCK_RECORD[f"{i.split('.')[0]}"] = track_dic
            print(track_dic)
            #print(os.path.join(root_directory, i))
            REVIEW_CO2_EMISSION.loc[n] = [order.split("\\")[1], dis , co2]
            n += 1
    #return jsonify({key: list(value.values()) for key, value in TARCK_RECORD.items()})
    REVIEW_CO2_EMISSION.to_excel("SUMMARY_2024_CO2_EMISSION.xlsx")

    return TARCK_RECORD

CARBON_CALCULATOR()
