import cx_Oracle
import pandas as pd 
import sqlite3


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
    query = f"SELECT * FROM sbs_pdc_mast"
    df = pd.read_sql_query(query, connection)
    return df

a = FETCH_DATA()
a.to_excel("SBS0470M.xlsx")