import pandas as pd
import requests, os, datetime
from io import BytesIO
from openpyxl import load_workbook
from pandas import ExcelWriter
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import numpy as np
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


key = "AIzaSyCAwn0vZV3u1r0DiLqrdlEZtSH17SuXmbg"
sheet_id = "19QiAzhDTTyNaZmSkUcemskQV2R9SUZRX"
excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

response = requests.get(excel_url)
cloud_file = BytesIO(response.content)

pack_data = pd.read_excel(cloud_file, sheet_name="Daily Record", engine="openpyxl")


file = "{}.xlsx".format(datetime.date.today())
base = r"Z:\業務部\業務一課\Q.工具程式\WESLEY\Experiment_Data"
path = os.path.join(base, file)

box_data = pd.read_excel(r"Z:\業務部\業務一課\Q.工具程式\WESLEY\Experiment_Data\Box Weight Data.xlsx")

pack_data["Box type"] = pack_data["Box type"].str.upper()
box_data = dict(zip(box_data["BOX_CODE"], box_data["CTN_WT"]))

pack_data["Box Weight"] = pack_data["Box type"].map(box_data)

# Only update Quantity if it is None (NaN) or 0
mask = (pack_data["Quantity"].isna()) | (pack_data["Quantity"] == 0)

pack_data.loc[mask, "Quantity"] = (
    (pack_data["Weight"] - pack_data["Box Weight"]) / pack_data["Weight per M"] * 1000
)

pack_data["Quantity"] = pack_data["Quantity"].fillna(0).astype(int)


pack_data.to_excel(path, index=False)
print("Successfully save the file {}".format(file))
