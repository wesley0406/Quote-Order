import cx_Oracle
import pandas as pd
import os
import numpy as np


def ERP_Connection(SQL):
    # Define connection details
    dsn = cx_Oracle.makedsn(
        host="192.168.1.242",      # Replace with your host IP or domain
        port=1526,                 # Replace with your port
        service_name="sperpdb"      # Replace with your service name
    )

    # Establish the connection
    connection = cx_Oracle.connect(
        user="spselect",          # Replace with your username
        password="select",        # Replace with your password
        dsn=dsn
    )

    # Execute SQL query and return dataframe
    df = pd.read_sql_query(SQL, connection)

    # Close connection
    connection.close()
    
    return df



def Concat_Cost_Sheet(FILE_PATH):

    DF_Cost_List = []

    for root, _, files in os.walk(FILE_PATH):
        for Cost_Files in files:
            if "成本表" in Cost_Files:
                file_path = os.path.join(root, Cost_Files)

                Cost_Workbook = pd.ExcelFile(file_path)
                Cost_Sheet_Name = [sheet for sheet in Cost_Workbook.sheet_names if "成本表" in sheet]

                for sheet in Cost_Sheet_Name:
                    DF_Cost_Sheet = pd.read_excel(file_path, sheet_name=sheet, header=3)
                    DF_Cost_Sheet.columns = DF_Cost_Sheet.columns.str.replace("\n", "") 
                    DF_Cost_List.append(DF_Cost_Sheet)

    if not DF_Cost_List: # Check if the DataFrame is empty
        raise ValueError(f"No valid '成本表' sheets found.")

    # This code should be at the same level as the "if" block above
    Summarized_Sheet = pd.concat(DF_Cost_List, axis=0, sort=False)

    return Summarized_Sheet


def MOQ_Counting(Quoting_Info):
	Quoting_Info["MOQ"] = 300/Quoting_Info["Weight_Per_Pcs"]
    # If MOQ > Quantity, revise quantity with its MOQ
    
	Quoting_Info["Size"] = Quoting_Info["Size"].astype(str).str.replace("X", "x")
	Quoting_Info["Length"] = Quoting_Info["Size"].apply(lambda x: x.split("x")[1] if "x" in x else None)
	Quoting_Info.loc[(Quoting_Info["Length"].astype(float) <= 100) & (Quoting_Info["MOQ"] < 100), "MOQ"] = 100 
	Quoting_Info.loc[(Quoting_Info["Length"].astype(float) > 100) & (Quoting_Info["MOQ"] < 50), "MOQ"] = 50
	# Roundup MOQ
	Quoting_Info["MOQ"] = Quoting_Info["MOQ"].apply(lambda x: int(np.ceil(x / 10) * 10) if pd.notna(x) else np.nan)

	Quoting_Info.loc[Quoting_Info["MOQ"] > Quoting_Info["Quantity"], "Quantity"] = \
        Quoting_Info.loc[Quoting_Info["MOQ"] > Quoting_Info["Quantity"], "MOQ"]

	# switch quantity from M to pcs for later filling up RFQ
	Quoting_Info["MOQ"] = (Quoting_Info["MOQ"].fillna(0) * 1000).astype(int)

	return Quoting_Info