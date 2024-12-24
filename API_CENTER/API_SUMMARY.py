import sys
import os
import sqlite3
import pandas as pd 
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import jsonify
import VERIFY_COST_STRUCTURE_ver2 as VCT
import QUOTATION_ANALYZE_API as QA 
from flask import Flask

app = Flask(__name__)

@app.route('/', methods=['GET'])
def VERIFY_COST():

	DB_address =  r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"
	root_dir = r"C:\Users\wesley\Desktop\workboard\Verifying_File"
	all_file = os.listdir(root_dir)
	whole_address = [os.path.join(root_dir, i) for i in all_file]
	PRODUCT_INFO, DATA_SUM, D1, D2, VER = QA.READ_FILE(whole_address[0])  # 檔案位置
	#VERIFTING_TABLE = DATA_SUM.loc[:, ["客戶代號", "M/盒", "USD/M\n(報價)", "線材\n(元/KG)", "利潤", "匯率"]]
	VERIFTING_TABLE = DATA_SUM.iloc[:, [1, 8, 51, 13, 43, 48]]
	OUTPUT = VCT.CREATE_HISTORY_TABLE(VERIFTING_TABLE).rename(columns = {"客戶代號" : "ITEM_CODE", "M/盒" : "Mpcs/CTN", "USD/M\n(報價)" : "USD/M", 
				"線材\n(元/KG)" : "LAST_WIRE_PRICE", "利潤" : "LAST_PROFIT_RATE", "匯率" : "LAST_EXCHANGE_RATE"}).to_dict()
	
	return jsonify({key: list(value.values()) for key, value in OUTPUT.items()})

# Register blueprints
#app.register_blueprint(posts_bp)
#app.register_blueprint(users_bp)

if __name__ == '__main__':
    app.run(debug=True)