import pandas as pd
import numpy as np
from math import pi
import time
from sqlalchemy import create_engine
import re, os
from fractions import Fraction



class FETCH_ERP_BOX():
	def __init__(self):
		self.oracle_connection_string = ("oracle+cx_oracle://spselect:select@192.168.1.242:1526/?service_name=sperpdb")
		self.engine = create_engine(self.oracle_connection_string)
		self.Box_ref = pd.read_excel(r"Z:\業務部\業務一課\Q.工具程式\CAYSIE\Box_ref.xlsx")
		self.package_df = self._fetch_package_weights()
		self.PREPARE_TRAIN_DATA_BOX()
		self.Result = None

	def PREPARE_TRAIN_DATA_BOX(self):
		required_columns_ERP = [
			"SC_NO",
			"CST_PART_NO", # 客戶產品代號
			"PDC_1",       # 產品種類
			"PDC_2",       # 外徑
			"PDC_3",       # 長度
			"UNIT_NAME",   # 計價單位(KG, LBS, M, PCS) drop the pcs since most of it is package
			"PDC_4",       # 變異碼(尾形)
			"PDC_5",       # 變異碼(華司)
			"PMT_NO",      # 外箱代號
			"QTY_PER_CTN", # 外箱可裝支數
			"SML_PMT_NO",  # 小盒代號
			"SMALL_PACK_QTY",  # 小盒可裝支數
			"PDC_1000_WT", # 單重
			"END_CODE"         # 是否為正確出貨品項
		]
		# reach all the box data in the ERP
		query = f"SELECT {', '.join(required_columns_ERP)} FROM ssl_cst_orde_d"
		ALL_HISTORY = pd.read_sql_query(query, self.engine.connect())
		ALL_HISTORY = ALL_HISTORY[
			(ALL_HISTORY["end_code"] != "D") & 
			(ALL_HISTORY["unit_name"] != "PCS")
		].copy()

		# connect the volume
		self.package_df = self.package_df.drop_duplicates(subset="pmt_no", keep="first")
		package_weights = self.package_df.set_index("pmt_no")["Volume(mm³)"]
		ALL_HISTORY["Carton_Volume"] = ALL_HISTORY["pmt_no"].map(package_weights)
		ALL_HISTORY["Box_Volume"] = ALL_HISTORY["sml_pmt_no"].map(package_weights)
		ALL_HISTORY = ALL_HISTORY.dropna(subset=["Carton_Volume", "Box_Volume"], how="all")
		ALL_HISTORY = ALL_HISTORY.dropna(subset=["qty_per_ctn", "small_pack_qty"], how="all")

		return ALL_HISTORY


	# filter the box size
	def extract_dimensions(self, text):
		match = re.search(r'(\d+)[x*×](\d+)[x*×](\d+)', text)
		if match:
			return f"{match.group(1)}*{match.group(2)}*{match.group(3)}"
		return None

	# calculate the box volumn
	def calculate_volume(self, dim_str):
		if dim_str:
			try:
				parts = dim_str.lower().replace("x", "*").split("*")
				l, w, h = map(int, parts)
				return l * w * h  # Volume in mm³
			except ValueError:
				return None
		return None

	# ERP 包材建檔
	def _fetch_package_weights(self):

		"""Fetch package weights from database"""
		query = "SELECT pmt_no, pck_spec FROM sbs_pck_mate "
		df_package = pd.read_sql_query(query, self.engine.connect())
		df_package["Dimension"] = df_package["pck_spec"].apply(self.extract_dimensions)
		df_package["Volume(mm³)"] = df_package["Dimension"].apply(self.calculate_volume)

		return df_package[["pmt_no", "Volume(mm³)"]]

# process the history data from the ERP back to 2016
class FETCH_ERP_SCREW(FETCH_ERP_BOX) :
	def __init__(self):
		super().__init__()
		self.HEAD_MAP = {
			"WUC" : "HEX",
			"W1" : "HEX",  
			"W5N" : "HEX",  
			"WUS" : "HEX", 
			"WSD" : "HEX", 
			"INH" : "HEX", 
			"FUC" : "HEX",
			"FH8" : "FLT",
			"FH9" : "FLT",
			"F12" : "FLT",
			"DBF" : "FLT",
			"FHU" : "FLT",
			"TR3" : "TRM",
			"TR6" : "TRM"
		}

		self.ALL_DATA = self.PREPARE_TRAIN_DATA_BOX().copy()
		self._fetch_screw_volume()

	def parse_diameter(self, val):
		if 'M' in val:
			return float(val.lstrip('M0')) / 10  # M0050 → 5.0 mm
		elif '#' in val:
			return (int(val.split('#')[1].lstrip('0'))*0.013+0.06)*25.4  # I#006 → #6 → 3.5052 mm
		else:
			return None

	# Function to parse length
	def parse_length(self, val, unit='mm'):
		fraction_map = {
			"0": 0,
			"4": 1/2,
			"5": 5/8,
			"6": 3/4,
			"1": 1/8,
			"2": 1/4,
			"3": 3/8,
			"7": 7/8
		}
		try:
			length = int(val.lstrip('0'))
			#print(length, type(length),unit)
			if unit == 'mm':
				return length / 10  # 00400 → 40.0 mm
			elif unit == 'inch':
				inches_len = int(length/1000)*25.4
				min_inches_len = float(Fraction(fraction_map.get(val[2], 0)))*25.4

				return (inches_len + min_inches_len) # 01000 → 1.0 inch → 25.4mm
		except:
			return None

	def estimate_screw_volume(self, diam, length):

		# Convert length to float
		if pd.isna(length) or length == "":
			#print(f"Invalid length: {length}. Must be non-empty and non-NaN.")
			return None
		# Validate inputs
		if pd.isna(diam) or diam == "" :
			#print(f"Invalid input: diameter={diam}. It must be positive.")
			return None

		# Calculate radius and volume
		radius = diam / 2
		volume = pi * (radius ** 2) * length
		return round(volume, 2)  # Round to 2 decimal places for readability

	def _get_weightTOquantity(self, row):
		unit = row.get("unit_name")
		qty_ctn = row.get("qty_per_ctn")
		qty_box = row.get("small_pack_qty")
		weight = row.get("pdc_1000_wt")

		if unit not in ("LBS", "KGS"):
			return row
		if not weight or weight == 0:  # catches None, 0, or NaN (if float)
			return row

		if unit == "LBS":
			converted_qty_ctn = qty_ctn / weight * 454
			converted_qty_box = qty_box / weight * 454
			
		else:  # unit == "KGS"
			converted_qty_ctn = qty_ctn / weight * 1000
			converted_qty_box = qty_box / weight * 1000


		row["qty_per_ctn"] = converted_qty_ctn
		row["small_pack_qty"] = converted_qty_box
		return row

	# Function to determine quantity and decision
	def get_quantity_and_volume(self, row):
		small_qty = row['small_pack_qty']
		ctn_qty = row['qty_per_ctn']
		box_vol = row['Box_Volume']
		carton_vol = row['Carton_Volume']
		
		# Check if small_pack_qty is valid (not null, not zero, numeric)
		if not pd.isna(small_qty) and small_qty != 0:
			try:
				qty = float(small_qty)
				if qty > 0:
					# Use Box_Volume, default to 0 if missing
					volume = float(box_vol) if not pd.isna(box_vol) else 0.0
					return qty*1000, volume
			except (ValueError, TypeError):
				print(f"Invalid small_pack_qty: {small_qty} for sc_no: {row['sc_no']}")
		
		# Fallback to qty_per_ctn
		try:
			qty = float(ctn_qty)
			if qty > 0:
				# Use Carton_Volume, default to 0 if missing
				volume = float(carton_vol) if not pd.isna(carton_vol) else 0.0
				if pd.isna(carton_vol):
					print(f"Missing Carton_Volume for sc_no: {row['sc_no']}")
				return qty*1000, volume
		except :
			#print(f"Invalid qty_per_ctn: {ctn_qty} for sc_no: {row['sc_no']}")
			print(f"No valid quantity for sc_no: {row['sc_no']}")
			return 0, 0.0
		

	def _fetch_screw_volume(self):

		# update the LBS & KGS quantity per box or CTN
		self.ALL_DATA = self.ALL_DATA.apply(self._get_weightTOquantity, axis =1)
		print("the original valid quantity from the ERP : {}".format(self.ALL_DATA.shape[0]))

		# Initialize new columns
		self.ALL_DATA['Screw volume in the box'] = 0.0
		self.ALL_DATA['decision box/master volume'] = 0.0
		
		# prepare the neccessary variable
		self.ALL_DATA['Diameter'] = self.ALL_DATA['pdc_2'].apply(self.parse_diameter)
		self.ALL_DATA['Length'] = self.ALL_DATA.apply(lambda row: 
						self.parse_length(row['pdc_3'], unit = 'inch' if '#' in row['pdc_2'] else 'mm'), axis=1)
		self.ALL_DATA["Screw_Type"] = self.ALL_DATA["pdc_1"].apply(lambda x : x[1:3])
		self.ALL_DATA["Head_Prototype"] = self.ALL_DATA["pdc_1"].apply(lambda x: x[6:9])
		self.ALL_DATA["Head_Type"] = self.ALL_DATA["Head_Prototype"].map(self.HEAD_MAP).fillna(self.ALL_DATA["Head_Prototype"])
		self.ALL_DATA["Screw_Volume"] = self.ALL_DATA.apply(lambda row : self.estimate_screw_volume(row['Diameter'], row["Length"]), axis = 1)

		# drop the invalid and washer product
		self.ALL_DATA = self.ALL_DATA.dropna(subset=["Screw_Volume"], how="all")


		# determine the screw volume and the final box/master
		for idx, row in self.ALL_DATA.iterrows():
			qty, volume = self.get_quantity_and_volume(row)
			screw_volume = row['Screw_Volume']
			
			# Calculate total screw volume if Screw_Volume is valid
			if not pd.isna(screw_volume) and screw_volume is not None:
				try:
					total_volume = float(screw_volume) * qty
					self.ALL_DATA.at[idx, 'Screw volume in the box'] = round(total_volume, 2)
				except (ValueError, TypeError):
					print(f"Invalid Screw_Volume: {screw_volume} for sc_no: {row['sc_no']}")
					self.ALL_DATA.at[idx, 'Screw volume in the box'] = 0.0
			else:
				print(f"Missing Screw_Volume for sc_no: {row['sc_no']}")
				self.ALL_DATA.at[idx, 'Screw volume in the box'] = 0.0
			
			self.ALL_DATA.at[idx, 'decision box/master volume'] = volume

		# calculate the empty ratio
		self.ALL_DATA["Packing_Ratio"] = self.ALL_DATA["Screw volume in the box"]/self.ALL_DATA["decision box/master volume"]

		# remove the unreasonable data (empty ration too small or beyond 100%)
		self.ALL_DATA = self.ALL_DATA.loc[(self.ALL_DATA["Packing_Ratio"] > 0.1) & (self.ALL_DATA["Packing_Ratio"] < 1)]


		# drop the invalid and washer product
		Required_Columns = ["Diameter", "Length", "Screw_Type", "Head_Type", "pdc_4", "pdc_5",
				"Screw volume in the box", "decision box/master volume", "Packing_Ratio"]
		HEAD = self.ALL_DATA["Head_Type"].drop_duplicates()
		#HEAD.to_excel("HEAD_TYPE.xlsx")

		cleaned_data = self.ALL_DATA.dropna(subset=["Packing_Ratio"], how="all")
		ERP_DATA = cleaned_data[~np.isinf(cleaned_data["Packing_Ratio"])]

		#ERP_DATA = cleaned_data[Required_Columns].copy()

		# add the real experiment data
		EXP = self._real_data()
		self.Result= pd.concat([ERP_DATA, EXP])

		self.Result.to_excel("Result_withcustomercode.xlsx")
		print("Current Quantity of the data : {}".format(self.Result.shape[0]))

	# training the real life data
	def _real_data(self) : 
		self.Box_Volume = pd.read_excel("Box_Choice.xlsx", sheet_name="ALL")
		EXP_DATA_PATH = r"C:\Users\wesley\Desktop\workboard\Volumn_Project\Experiment_Data"
		data_list = []
		for file in os.listdir(EXP_DATA_PATH) : 
			try : 
				daily_data = pd.read_excel(os.path.join(EXP_DATA_PATH, file))
				Required_Data = daily_data[["Screw_Type", "Head_Type", "pdc_4", "pdc_5", "Diameter", "Length", "Quantity", "Box type"]]
				data_list.append(Required_Data)

			except (ValueError, TypeError) as e:
				print("gor the error code : {}".format(e))

		# Combine all data into one DataFrame
		SUM_df = pd.concat(data_list, ignore_index=True)

		# preprocess to concat the ERP Data
		def parse_length(length, unit = "mm"):
			if unit == "mm" :
				return float(length)
			else:
				if "-" in str(length):
					full, partial = length.split("-")
					return int(full) * 25.4 + float(Fraction(partial)) * 25.4
				elif "/" in str(length):
					return float(Fraction(length)) * 25.4
				else:
					return float(length) * 25.4  # assume it's a pure inch number
		def parse_diameter(val) : 			
			if 'M' in val:
				return float(val.lstrip('M'))  # M0050 → 5.0 mm
			elif '#' in val:
				return (int(val.split('#')[1])*0.013+0.06)*25.4  # I#006 → #6 → 3.5052 mm
			else:
				return None

		SUM_df["Length"] = SUM_df.apply(lambda row: 
						parse_length(row['Length'], unit = 'inch' if '#' in row['Diameter'] else 'mm'), axis=1)
		SUM_df["Diameter"] = SUM_df['Diameter'].apply(parse_diameter)
		SUM_df["Screw_Volume"] = SUM_df.apply(lambda row : self.estimate_screw_volume(row['Diameter'], row["Length"]), axis = 1)
		SUM_df["Screw volume in the box"] = SUM_df["Screw_Volume"]*SUM_df["Quantity"]
		SUM_df["decision box/master volume"] = SUM_df["Box type"].map(self.Box_Volume.set_index("Quote_Code")["Volume"]).apply(self.calculate_volume)
		SUM_df["Packing_Ratio"] = SUM_df["Screw volume in the box"]/SUM_df["decision box/master volume"]
		
		return SUM_df


if __name__ == "__main__":
	start = time.time()
	bot = FETCH_ERP_SCREW()
	#bot._fetch_screw_volume()
	print("耗時{}".format(time.time()- start))