import pandas as pd 
import os, re , sys
import time
from datetime import datetime
import sqlite3
import unicodedata

# Define the root directory where your files are located
root_directory = "Z:/業務部/業務一課/G-報價/1. 外銷/"


def FIND_FOLDER(root):
	FOLDER_PATH = []
	COST_FILE_PATH = []
	# Walk through the directory structure|
	for dirpath, dirnames, _ in os.walk(root):
		for dirname in dirnames:
			if dirname in ["2024", "2025"]:
				FOLDER_PATH.append(os.path.join(dirpath, dirname))
	for folder in FOLDER_PATH :
		for dirpath, _, filenames in os.walk(folder):
			COST_FILE_PATH.extend([os.path.join(dirpath, file) for file in filenames if '成本表' in file])

	return FOLDER_PATH, [path for path in COST_FILE_PATH if "~$" not in path]

# Find all folders named "2024"
def CALCULATE_FILE(root_path):
	start = time.time()
	FOLDER, COST = FIND_FOLDER(root_path)
	end = time.time()
	print("搜尋共耗費 : {}秒".format(end - start))
	return COST

# 拆解檔案名稱
def NAME_CATEGORY(FILE_PATH) :
	NAME = FILE_PATH.split("\\")[-1]
	CUSTOMER = NAME.split("-")[1]	#客戶代號
	AGENT = NAME.split("-")[2]	  #承辦人員
	DATE = NAME.split("-")[3]		#詢價日期
	ORDER_INFO = NAME.split("-")[4] #單號或是對接窗口
	return [CUSTOMER.ljust(6,"0"), AGENT, DATE, ORDER_INFO[1], ORDER_INFO[3:].replace(".xlsx","")]

# 找出中文品名
def DESCRIPTION_CHINESE(PN_TOTAL) :
	DESCRIPTION = []
	CATOGORY_QUANTITY = []
	for number in range(len(PN_TOTAL) - 1):
		item_num = PN_TOTAL.index[number+1] - PN_TOTAL.index[number]
		CATOGORY_QUANTITY.append(item_num)
	CATOGORY_QUANTITY[0] += 2	
	for number in range(len(CATOGORY_QUANTITY)):
		DESCRIPTION.append([PN_TOTAL.values[number]]*CATOGORY_QUANTITY[number])
	return  [item for i in DESCRIPTION for item in i ]

# 讀成本表檔案
def READ_FILE(FILE_PATH) :
	STANDARD_PRODUCT_INFO = list(range(52))
	SHEET_NAME = "成本表 "
	with pd.ExcelFile(FILE_PATH) as MOTHER:
		for i in MOTHER.sheet_names:
			if "成本" in i :
				SHEET_NAME = i
				
		# read file and skip the first row
		ROUGH = pd.read_excel(MOTHER, SHEET_NAME, header=None, skiprows=1, usecols = STANDARD_PRODUCT_INFO) 
		THRESHOLD_Nan = 2				  
		if "品名" not in str(ROUGH.iloc[1, 1]) or "報價日" not in str(ROUGH.iloc[0,1]) or "回饋金" not in str(ROUGH.iloc[2,50]) :
			print("此檔案不合標準規範 : {}".format(FILE_PATH.split("\\")[-1]))
		else:	  
		# find quote date
			#print(unicodedata.normalize('NFKC', str(ROUGH.iloc[0, 1])))
			QUOTE_DATE = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 1])).split(":")[1]  # 報價日
			VALID_DATE = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 6])).split(":")[1]	# 報價有效日
			VERIFICATION = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 13])).split(":")[1] # 稽核人
			try:
				NOTE = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 22])).split(":")[1] # 備註
			except :
				NOTE = None
		# find the product type
			PN_INDEX = ROUGH[ROUGH[ROUGH.columns[1]].astype(str).str.contains('品名', na=False)].index 
			PN_TOTAL = ROUGH[1][PN_INDEX]
			PN_TOTAL = PN_TOTAL._append(pd.Series(["Bottom"],[ROUGH.index[-1]]))
			ROUGH["53"] = DESCRIPTION_CHINESE(PN_TOTAL)	# 新增中文敘述
		# Count NaN values in each row and drop rows with more than 2 NaNs then remove it 
			Nan_DROP = ROUGH[ROUGH.isnull().sum(axis=1) > THRESHOLD_Nan].index
			RAW = ROUGH.drop(Nan_DROP)
		# remove the column name	
			DELETE_ROW = RAW.index[[0]]	
			Nan_rows = RAW[RAW[RAW.columns[0]].isnull()].index
			DELETE_ROW = DELETE_ROW.append(Nan_rows)
			RAW.columns = RAW.iloc[0]			# set column
			CLEAN_SHEET = RAW.drop(DELETE_ROW) # remove the column name and sigature
			CLEAN_SHEET = CLEAN_SHEET.rename(columns = {CLEAN_SHEET.columns[-1]:"中文敘述"})
			CLEAN_SHEET = CLEAN_SHEET.rename(columns = {CLEAN_SHEET.columns[0]:"詢價品項編號"})
			CLEAN_SHEET["詢價單地址"] = [FILE_PATH] * CLEAN_SHEET.shape[0]
			CLEAN_SHEET["日期"] = [NAME_CATEGORY(FILE_PATH)[2]] * CLEAN_SHEET.shape[0]
			CLEAN_SHEET["ORDER_TYPE"] = [NAME_CATEGORY(FILE_PATH)[3]] * CLEAN_SHEET.shape[0]
			CLEAN_SHEET["AGENT"] = [NAME_CATEGORY(FILE_PATH)[1]] * CLEAN_SHEET.shape[0] #製表人
			CLEAN_SHEET["CUSTOMER_CODE"] = [NAME_CATEGORY(FILE_PATH)[0]] * CLEAN_SHEET.shape[0] #客代
			CLEAN_SHEET["ORDER_NUMBER"] = [NAME_CATEGORY(FILE_PATH)[4]] * CLEAN_SHEET.shape[0] #單號
			CLEAN_SHEET["NOTE"] = NOTE
			#print("報價單名字 :{}".format(FILE_PATH.split("\\")[-1]))
			#print("此筆報價共含 :{} 筆產品".format(CLEAN_SHEET.shape[0]))
			return PN_TOTAL, CLEAN_SHEET, QUOTE_DATE, VALID_DATE, VERIFICATION

# 統整此次詢價
def PRODUCT_SUMMARY(PANDAS_SERIES, TOTAL_AMOUNT):
	CUMULATIVE = 0
	for number in range(len(PANDAS_SERIES)-1):
		item_num = PANDAS_SERIES.index[number+1] - PANDAS_SERIES.index[number] - 3
		CUMULATIVE += item_num
		print("{} 此次詢價項次 : {} 項".format(PANDAS_SERIES.values[number], item_num))

# 取出中文品名
def SCREW_TYPE(PANDA_SERIE):
	pattern = r'[^品名]([^螺絲\s]+)\s*螺絲' 
	type_list = []
	for i in range(len(PANDA_SERIE)):
		match = re.search(pattern, PANDA_SERIE.values[i])
		if match:
			type_list.append(match.group(1).strip())
	return list(set(type_list))

# 將成本表的品項輸入資料庫中
def QUOTATION_INSERT(DATAFRAME, TABLENAME, DBNAME, VERNIER):
	COLUMNS = ['PRODUCT_CODE', 'DRAWING_NUMBER', 'SIZE', 'RECESS_PARTIAL_THREAD',
		'MOQ', 'QUANTITY', 'WEIGHT', 'M_BOX', 'KG_BOX', 'BOX_TYPE', 'BOX_PRICE',
		'WIRE_DIAMETER', 'WIRE_PRICE', 'FORMING_PRICE', 'FORMING_PIECE_WEIGHT',
		'FORMING_TOTAL', 'FORMING_GROSS', 'CUT_SLUTTING_LOSS',
		'CUT_SLUTTING_PRICE_M', 'CUT_SLUTTING_PRICE_KG', 'CUT_SLUTTING_GROSS',
		'HEAT_TREATMENT_LOSS', 'HEAT_TREATMENT_PRICE', 'HEAT_TREATMENT_GROSS',
		'PLATING_LOSS', 'PLATING_PRICE_KG', 'PLATING_GROSS', 'PACKAGE_LOSS',
		'PACKAGE_PRICE', 'PACKAGE_GROSS', 'TRANSACTION_CONDITION',
		'OPERATION_FEE', 'FIRST_GROSS', 'ROLLER_SORTING_LOSS',
		'ROLLER_SORTING_PRICE', 'ROLLER_SORTING_GROSS_KG',
		'ROLLER_SORTING_GROSS_M', 'OPTICAL_SORTING_LOSS',
		'OPTICAL_SORTING_PRICE', 'OPTICAL_SORTING_GROSS_M', 'INTEREST_RATE',
		'INTEREST_GROSS',  'PROFIT_RATE', 'PROFIT_GROSS', 'COLLATED_LOSS', 
		'COLLATED_PRICE', 'COLLATED_GROSS', 'EXCHANGE_RATE', 'EXCHANGE_RATE_GROSS',
		'REBATE', 'TOTAL_PRICE_M', 'DESCRIPTION', 'ORDER_ADDRESS', 'QUOTE_DATE',
		'ORDER_TYPE', "AGENT", "CUSTOMER_CODE", "ORDER_NUMBER", "NOTE" ,"SERIAL_NUMBER"]

	for quote_item in DATAFRAME.index:
		ROW_INSERT = DATAFRAME.loc[quote_item,:].values.flatten().tolist()
		ROW_INSERT.pop(0)
		ROW_INSERT.append(datetime.now().timestamp())
		query = f"INSERT INTO {TABLENAME} ({', '.join(COLUMNS)}) VALUES ({', '.join(['?']*len(ROW_INSERT))});"
		VERNIER.execute(query, ROW_INSERT)
		time.sleep(0.1)

# 取用database中的list，確認檔案是否已讀取
def CHECK_FILE(DATABASE, TABLE):
	with sqlite3.connect(DATABASE) as connection :
		cursor = connection.cursor()
		# Replace 'your_table_name' and 'your_column_name' with the actual table and column names
		column_name = "FILE_ADDRESS"
		# Check if the value already exists in the specified column
		query = f"SELECT {column_name} FROM {TABLE};"
		#existing_rows = cursor.execute(query).fetchall()
		df = pd.read_sql_query(query, connection)
	return df

def QUOTATION_ANALYZE(COST_FILE_PATH):
	# 詢價統計表打底
	exception_count = 0
	DATABASE = r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"
	ORDER_ADDRESS_LIST = CHECK_FILE(DATABASE, "PRODUCT_ADDRESS_SUMMARY" )
	BASE = pd.DataFrame(columns=["承辦人", "稽核人", "詢價日", "報價日", "有效日", "客戶代號", "詢價單號",
								"產品類別", "線材價格", "利潤", "匯率", "幣別","詢價重量", "報價產品項次",
								"下單重量", "接單率", "接單項次", "接單率","客戶訂單編號"])
	for file_path in COST_FILE_PATH:
		if file_path.split("\\")[-1][:3] == "成本表" : 
			INSERT_ROW = []
			try:
				PRODUCT_INFO, DATA_SUM, D1, D2, VER = READ_FILE(file_path)
				if  file_path not in ORDER_ADDRESS_LIST["FILE_ADDRESS"].values :	 #如果此成本表不在資料庫中，新增至資料庫
					print("\n此次更新檔案 : {}\n".format(file_path))
					with sqlite3.connect(DATABASE) as connection : 
						cursor = connection.cursor()
						cursor.execute(f"INSERT INTO PRODUCT_ADDRESS_SUMMARY (FILE_ADDRESS) VALUES (?);"
									 ,(file_path,))                                            # 檔案位置資料庫
						QUOTATION_INSERT(DATA_SUM, "CUSTOMER_PRODUCT_SUMMARY", DATABASE, cursor)#品項資料庫
				else :
					pass

				QUOTE_NAME = NAME_CATEGORY(file_path.split("\\")[-1])
				INSERT_ROW.append([QUOTE_NAME[1], VER,	 #稽核人, 承辦人
									QUOTE_NAME[2],  #詢價日
									D1, D2,		    #報價日, 有效日
									QUOTE_NAME[0],  #客戶代號
									QUOTE_NAME[4],  #詢價單號
									SCREW_TYPE(PRODUCT_INFO),		    #產品類別
									DATA_SUM["線材\n(元/KG)"].unique(),  #線材價格
									DATA_SUM["利潤"].unique(),		    #利潤
									DATA_SUM["匯率"].unique(),		    #匯率
									DATA_SUM.columns[-2].split("/")[0], #幣別
									DATA_SUM["重量(KG)"].sum(),		    #詢價重量
									DATA_SUM.shape[0],				    #報價產品項次
									0, 0, 0, 0, 0])					    #訂單相關
				BASE = pd.concat([pd.DataFrame(INSERT_ROW, columns = BASE.columns), BASE], ignore_index=True)
			except Exception as e:
				exception_count += 1
				# Print the error code (exception details)
				print(f"An error occurred: {file_path}")
				print(f"Error type: {type(e).__name__} : {e}")
				if exception_count >= 50:
					print("Exception limit exceeded. Shutting down the program.")
					sys.exit(1)  # Exit the program with an error status

	
	ALL_QUOTE = BASE.sort_values(by = ["詢價日"]).reset_index().drop(columns = "index")
	#ALL_QUOTE.to_excel("詢價統計表.xlsx", index = False)
	return DATA_SUM

# 以成本表路徑更新資料庫
# def UPDATEDB_BYFILE(DB,ROW_NAME) :
# 	with sqlite3.connect(DB) as connection :
# 		cursor = connection.cursor()
# 		# delete old data
# 		cursor.execute(f"DELETE FROM PRODUCT_ADDRESS_SUMMARY WHERE FILE_ADDRESS ='{ROW_NAME}'")
# 		cursor.execute(f"DELETE FROM CUSTOMER_PRODUCT_SUMMARY WHERE ORDER_ADDRESS ='{ROW_NAME}'")

# 		#reload the data into DB
# 		PRODUCT_INFO, DATA_SUM, D1, D2, VER = READ_FILE(ROW_NAME)
# 		cursor.execute(f"INSERT INTO PRODUCT_ADDRESS_SUMMARY (FILE_ADDRESS) VALUES (?);"
# 										 ,(ROW_NAME,)) # 檔案位置資料庫
# 		QUOTATION_INSERT(DATA_SUM, "CUSTOMER_PRODUCT_SUMMARY", "QUOTATION_DATABASE.db", cursor)
#  