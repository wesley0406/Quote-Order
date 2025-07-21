import pandas as pd
import requests
from io import BytesIO
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# --------- Step 1: Read Google Sheet as Excel file ---------
sheet_id = "19QiAzhDTTyNaZmSkUcemskQV2R9SUZRX"
excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

response = requests.get(excel_url)
cloud_file = BytesIO(response.content)

pack_data = pd.read_excel(cloud_file, sheet_name="Daily Record", engine="openpyxl")

# Example screws DataFrame
screws = pd.DataFrame({
    "Type": ["Wood", "Metal", "Plastic"],
    "Length (mm)": [20, 30, 15],
    "Stock": [100, 150, 200]
})

# Optional: Text result to write into A1
result = "Screw inventory updated"

# --------- Step 2: Authenticate with Google Sheets API ---------
creds = Credentials.from_service_account_file("C:/Users/wesley/Desktop/workboard/Volumn_Project/credentials.json", scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

# --------- Step 3: Open spreadsheet ---------
spreadsheet = client.open_by_key(sheet_id)

# --------- Step 4: Access or create 'screws' worksheet ---------
try:
    worksheet_screws = spreadsheet.add_worksheet(title="screws", rows=100, cols=20)
except gspread.exceptions.APIError:
    worksheet_screws = spreadsheet.worksheet("screws")

# Optional: Clear existing content before writing
worksheet_screws.clear()

# --------- Step 5: Write DataFrame to the 'screws' worksheet ---------
set_with_dataframe(worksheet_screws, screws)

# --------- Step 6: Write text to cell A1 ---------
worksheet_screws.update("A1", result)