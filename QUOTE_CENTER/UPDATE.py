import tkinter as tk
from tkinter import messagebox
import UPDATE_DB_FUNC as UDF
import os
import sqlite3
from contextlib import redirect_stdout
import io
#pyinstaller --onefile --windowed --icon=icon.ico TEST_APP.py
DB = r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"

def UPDATEDB_BYFILE():
    try:
        file_path = file_entry.get()
        if not file_path:
            result_label.config(text="Please enter a valid file address.")
            return

        with sqlite3.connect(DB) as connection:
            cursor = connection.cursor()

            # Delete old data
            cursor.execute(
                f"DELETE FROM PRODUCT_ADDRESS_SUMMARY WHERE FILE_ADDRESS = ?",
                (file_path,)
            )
            cursor.execute(
                f"DELETE FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_ADDRESS = ?",
                (file_path,)
            )

            # Reload the data into DB
            PRODUCT_INFO, DATA_SUM, D1, D2, VER = UDF.READ_FILE(file_path)
            cursor.execute(
                "INSERT INTO PRODUCT_ADDRESS_SUMMARY (FILE_ADDRESS) VALUES (?);",
                (file_path,)
            )

            # Assuming QUOTATION_INSERT is defined in UPDATE_DB_FUNC
            UDF.QUOTATION_INSERT(DATA_SUM, "CUSTOMER_PRODUCT_SUMMARY", "QUOTATION_DATABASE.db", cursor)

            result_label.config(text=f"Updated file: {os.path.basename(file_path)} successfully")
    except Exception as e:
        result_label.config(text=f"Error: {e}")

def WEEKLY_RENEW():
    try:
        output = io.StringIO()
        with redirect_stdout(output):
            COST = UDF.CALCULATE_FILE(r"Z:/業務部/業務一課/G-報價/1. 外銷/C03000 ESSVE/2024")
            SUMMARY = UDF.QUOTATION_ANALYZE(COST)
        WEEKLY_REPORT.config(text=output.getvalue())
    except Exception as e:
        WEEKLY_REPORT.config(text=f"Error: {e}")

# Initialize the main app window
app = tk.Tk()
app.title("QUICK_UPDATER")
app.geometry("800x600")

# Add an icon
try:
    app.iconbitmap('icon.ico')
except:
    print("Icon file not found, skipping...")

# Create widgets
frame = tk.Frame(app)
frame.pack()

tk.Label(frame, text="Enter file address:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
file_entry = tk.Entry(frame, width=80)
file_entry.grid(row=1, column=0, padx=10, pady=10)

update_button = tk.Button(frame, text="Update Database Through File", command=UPDATEDB_BYFILE)
update_button.grid(row=2, column=0, pady=10)

# weekly_report_button = tk.Button(frame, text="Generate Weekly Report", command=WEEKLY_RENEW)
# weekly_report_button.grid(row=3, column=0, pady=10)

# Labels for result and report
result_label = tk.Label(frame, text="", fg="green")
result_label.grid(row=4, column=0, pady=10)

# WEEKLY_REPORT = tk.Label(frame, text="", wraplength=700, justify="left")
# WEEKLY_REPORT.grid(row=5, column=0, pady=20)

app.mainloop()




 
