import UPDATE_DB_FUNC as UDF 
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import jsonify, Flask, render_template_string
import os, sys, io 
from contextlib import redirect_stdout

#test_path = [r"Z:\\業務部\\業務一課\\G-報價\\1. 外銷\\C01100 Interfix\\2024\\20240821\\成本表-C01101-Wesley-20240821-(E)Edward.xlsx",
#			r"Z:/業務部/業務一課/G-報價/1. 外銷/C03400 Index\2024\REMAKE\成本表-C034-Rebecca-20230801-(S) SDS+EPDM.xlsx",
#			r"Z:/業務部/業務一課/G-報價/1. 外銷/C01900 Reyher\2024\REMAKE\成本表-C01900-Rebecca-20220218 6000827531 乾牆螺絲 (專案906).xlsx"]
app = Flask(__name__)

@app.route('/UPDATE_DB', methods=['GET'])
def UPDATE_DB():
	FILE_PATH = r"Z:/業務部/業務一課/G-報價/1. 外銷/"
	COST = UDF.CALCULATE_FILE(FILE_PATH)
	output = io.StringIO()
	with redirect_stdout(output):
		SUMMARY = UDF.QUOTATION_ANALYZE(COST)
	output_str = output.getvalue()
	return render_template_string('''
	<html>
		<head>
			<title>Function Output</title>
		</head>
		<body>
			<h1>UPDATE RESULT :</h1>
			<pre>{{ output }}</pre>
		</body>
	</html>
	''', output = output_str)

if __name__ == '__main__':
	app.run(debug=True)
