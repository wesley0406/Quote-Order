

import pandas as pd 
import os 
import re 
import time
from datetime import datetime
import sqlite3
import unicodedata

def NAME_CATEGORY(FILE_PATH) :
    NAME = FILE_PATH.split("\\")[-1]
    CUSTOMER = NAME.split("-")[1]   #客戶代號
    AGENT = NAME.split("-")[2]      #承辦人員
    DATE = NAME.split("-")[3]       #詢價日期
    ORDER_INFO = NAME.split("-")[4] #單號或是對接窗口
    return [CUSTOMER.ljust(6,"0"), AGENT, DATE, ORDER_INFO[1], ORDER_INFO[3:].replace(".xlsx","")]


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
            VALID_DATE = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 6])).split(":")[1]   # 報價有效日
            VERIFICATION = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 13])).split(":")[1] # 稽核人
            try:
                NOTE = unicodedata.normalize('NFKC',str(ROUGH.iloc[0, 22])).split(":")[1] # 備註
            except :
                NOTE = None
        # find the product type
            PN_INDEX = ROUGH[ROUGH[ROUGH.columns[1]].astype(str).str.contains('品名', na=False)].index 
            PN_TOTAL = ROUGH[1][PN_INDEX]
            PN_TOTAL = PN_TOTAL._append(pd.Series(["Bottom"],[ROUGH.index[-1]]))
            ROUGH["53"] = DESCRIPTION_CHINESE(PN_TOTAL)   # 新增中文敘述
        # Count NaN values in each row and drop rows with more than 2 NaNs then remove it 
            Nan_DROP = ROUGH[ROUGH.isnull().sum(axis=1) > THRESHOLD_Nan].index
            RAW = ROUGH.drop(Nan_DROP)
        # remove the column name    
            DELETE_ROW = RAW.index[[0]]    
            Nan_rows = RAW[RAW[RAW.columns[0]].isnull()].index
            DELETE_ROW = DELETE_ROW.append(Nan_rows)
            RAW.columns = RAW.iloc[0]           # set column
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


def PRODUCT_SUMMARY(PANDAS_SERIES, TOTAL_AMOUNT):
    CUMULATIVE = 0
    for number in range(len(PANDAS_SERIES)-1):
        item_num = PANDAS_SERIES.index[number+1] - PANDAS_SERIES.index[number] - 3
        CUMULATIVE += item_num
        print("{} 此次詢價項次 : {} 項".format(PANDAS_SERIES.values[number], item_num))
    return       



