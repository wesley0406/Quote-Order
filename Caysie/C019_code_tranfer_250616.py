import pandas as pd
import os
import sqlite3
import cx_Oracle
import re
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from sqlalchemy import create_engine

# DB_CONFIG = {
	# 	"host": "192.168.1.242",
	# 	"port": 1526,
	# 	"service_name": "sperpdb",
	# 	"user": "spselect",
	# 	"password": "select"
	# }

class CODE_TRANSFER:
	def __init__(self, path):
		self.PATH = path
		self.COMPARE_FILE = self.load_compare_file()
		self.Original = None

	# 讀取新舊產品代號比較表	
	def load_compare_file(self):
		compare_path = r"Z:\業務部\業務一課\G-報價\1. 外銷\C01900 Reyher\2025\C019 新舊產品代號對照表_Caysie.xlsx"
		sheet_names = ["MS", "SDS", "TT", "DW", "CB", "TP"]
		dic_item_series = pd.read_excel(compare_path, sheet_name=None, dtype=str)
		return pd.concat([dic_item_series[s] for s in sheet_names], ignore_index=True)

	# 讀取客人原始詢價單或訂單
	def load_customer_file(self):
		for file in os.listdir(self.PATH):
			if "_RFQ_" in file:
				path = os.path.join(self.PATH, file)
				self.Original = pd.read_excel(path, sheet_name="RFQ positions", skiprows=9)
				print(f"Loaded RFQ file: {file}")
				return
			elif "PO_" in file:
				path = os.path.join(self.PATH, file)
				self.Original = pd.read_excel(path, sheet_name="Bestellpositionen", skiprows=1)
				print(f"Loaded PO file: {file}")
				return
		raise FileNotFoundError("No '_RFQ_' or 'PO_' file found in the given path.")

	# 產出舊產品代號
	def find_old_code(self):
		self.Original["original_category"] = self.Original["Material"].astype(str).apply(lambda x: ".".join(x.split(".")[:2]))
		for num, item_cat in self.Original["original_category"].items():
			match = self.COMPARE_FILE[self.COMPARE_FILE["新產品代號"] == item_cat]
			if not match.empty:
				self.Original.at[num, "old_category"] = match.iloc[0]["舊產品代號"]
		self.Original["material_suffix"] = self.Original["Material"].astype(str).apply(lambda x: ".".join(x.split(".")[2:]))
		self.Original["previous_item_code"] = self.Original["old_category"].astype(str) + "." + self.Original["material_suffix"]
		return self.Original


class RFQ_CODE_TRANSFER(CODE_TRANSFER):
	required_columns_ERP = [
		"CST_PART_NO",
		"PDC_1",
		"DLV_DATE",
		"PMT_NO",
		"QTY_PER_CTN"
	]

	def __init__(self, path):
		super().__init__(path)
		self.load_customer_file()
		self.db_data = self.load_db_data()

	def FIND_ERP(self, ITEM_CODE):
		# the file for the box comparison
		Box_ref = pd.read_excel(r"Z:\業務部\業務一課\Q.工具程式\CAYSIE\Box_ref.xlsx")
		Mapping_box = dict(zip(Box_ref["ERP_CODE"], Box_ref["Quote_Code"]))
		query = f"SELECT {', '.join(self.required_columns_ERP)} FROM ssl_cst_orde_d WHERE CST_PART_NO = '{ITEM_CODE}' ORDER BY DLV_DATE DESC"
		oracle_connection_string = (
		   "oracle+cx_oracle://spselect:select@192.168.1.242:1526/?service_name=sperpdb")
		engine = create_engine(oracle_connection_string)

		with engine.connect() as connection:
			history_data = pd.read_sql_query(query, connection)
			history_data.columns = [col.upper() for col in history_data.columns]
			if history_data.empty:
				return None
			history_data["QTY_PER_CTN"] = history_data["QTY_PER_CTN"]*1000
			history_data["PMT_NO"] = history_data["PMT_NO"].map(Mapping_box).fillna(history_data["PMT_NO"])


		return history_data.iloc[0, :]

	# 讀取所有報價資料庫內的客戶代號為C019的資料
	def load_db_data(self):
		db_path = r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"
		with sqlite3.connect(db_path) as conn:
			return pd.read_sql_query("SELECT PRODUCT_CODE FROM CUSTOMER_PRODUCT_SUMMARY WHERE CUSTOMER_CODE = 'C01900'", conn)

	#取得用於跑小工具轉出成本表之最新代號，以新代號優先、舊代號僅次、皆未找到則顯示"Not found"
	def get_search_code(self):
		df = self.find_old_code().copy()
		product_codes = set(self.db_data["PRODUCT_CODE"])
		
		df["SEARCHING_CODE"] = "Not found"
		df.loc[df["previous_item_code"].isin(product_codes), "SEARCHING_CODE"] = df["previous_item_code"]
		df.loc[df["Material"].isin(product_codes), "SEARCHING_CODE"] = df["Material"]
		
		output_file = os.path.join(self.PATH, "Updated_RFQ.xlsx")
		cols = ["Item", "Material", "previous_item_code", "Description", "RFQ Quantity", "Package Qty", "SEARCHING_CODE"]

		# add  the previouse ERP result 
		result = df[cols].copy()
		result["Previouse_Box"] = None
		result["Previouse_Box_Quantity"] = None
		for num, item in result["previous_item_code"].items():
			ERP_feedback = self.FIND_ERP(item)
			if ERP_feedback is not None :
				result.at[num, "Previouse_Box"] = ERP_feedback["PMT_NO"]
				result.at[num, "Previouse_Box_Quantity"] = ERP_feedback["QTY_PER_CTN"]


		result.to_excel(output_file, index=False)
		with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
			result.to_excel(writer, index=False, sheet_name='Sheet1')
			workbook = writer.book
			worksheet = writer.sheets['Sheet1']

			red_format = workbook.add_format({'bg_color': '#FF0000'})

			for row in range(1, len(result) + 1):  # +1 to offset header
				pkg_cell = f'F{row + 1}'  # +1 because Excel rows are 1-based and row 1 is header
				prev_cell = f'I{row + 1}'
				worksheet.conditional_format(prev_cell, {
		            'type': 'formula',
		            'criteria': f'=${pkg_cell}<>${prev_cell}',
		            'format': red_format
		        })


class PO_CODE_TRANSFER(CODE_TRANSFER):
	def __init__(self, path):
		super().__init__(path)
		self.load_customer_file() #確保啟動功能時，客戶原始檔案同步讀取
		self.customer_items = self.fetch_customer_items()

	#連結ERP 0605M 取得曾出貨且客戶代號為C01900之所有客戶產品代號 (0210M尚未有table可拉)
	def fetch_customer_items(self):
		dsn = cx_Oracle.makedsn("192.168.1.242", 1526, service_name="sperpdb")
		conn = cx_Oracle.connect(user="spselect", password="select", dsn=dsn)
		df = pd.read_sql_query("SELECT CST_PART_NO FROM v_ssl0605q_cst WHERE ORD_CST_NO = 'C01900'", conn)
		conn.close()
		return df.drop_duplicates(subset=["CST_PART_NO"])

	# 比對0605M後，若客人已以新代號下過單顯示"New Item Code exist"；
	# 若無則顯示舊產品代號；舊產品代號不存在時顯示"初次下單"
	def set_item_code(self):
		df = self.find_old_code().copy()
		new_code = df["Material"].isin(self.customer_items["CST_PART_NO"])
		old_code = df["previous_item_code"].isin(self.customer_items["CST_PART_NO"])
		df["set_code"] = "初次下單"
		df.loc[old_code, "set_code"] = df.loc[old_code, "previous_item_code"]
		df.loc[new_code, "set_code"] = "New Item Code exist"

		cols = ["Purchasing Doc.", "Item", "Material", "set_code", "Description 2", "PO Quantity"]
		df[cols].to_excel(os.path.join(self.PATH, "Set_Item_Code.xlsx"), index=False)



if __name__ == "__main__":
	path = input("Enter folder path: ").strip()

	#根據路徑判斷要啟動之功能
	if "報價" in path:
		rfq_bot = RFQ_CODE_TRANSFER(path)
		rfq_bot.get_search_code()
		print("Updated_RFQ saved in path.")

	elif "訂單" in path:
		po_bot = PO_CODE_TRANSFER(path)
		po_bot.set_item_code()
		print("Check to-be-set-codes file in path.")

	else:
		print("Unable to define '報價' or '訂單'")

	
