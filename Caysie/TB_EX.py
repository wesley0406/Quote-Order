import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from datetime import datetime
from openpyxl import Workbook
import openpyxl

def RETAIN_EX() :
	url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

	# Step 1: Fetch HTML
	response = requests.get(url)
	soup = BeautifulSoup(response.text, "html.parser")

	# Step 2: Find the table
	table = soup.find("table", {"title": "牌告匯率"})

	# Step 3: Extract rows
	rows = table.tbody.find_all("tr")

	data = []
	for row in rows:
		cols = row.find_all("td")
		currency_code = cols[0].find("div", class_="visible-phone print_hide").text.strip().strip("()")
		spot_buy = cols[3].text.strip()

		data.append({
			# "Currency": currency_name,
			"Code": currency_code,
			"Spot Buy": spot_buy,
		})

	# Step 4: Turn into DataFrame
	df = pd.DataFrame(data)
	USD_EX = df.loc[0, "Spot Buy"]
	EURO_EX = df.loc[14, "Spot Buy"]
	
	return USD_EX, EURO_EX, datetime.today().strftime("%#m/%#d")

if __name__ == "__main__":
	USD, EURO, today = RETAIN_EX()  # today is in "6/18" format (string)
	root_sum = r"Z:\業務部\業務一課\G-報價\3. 詢價統計\詢價單統計表-For2025"
	wb = openpyxl.load_workbook("詢價單統計表_test.xlsx")
	sheet = wb.worksheets[0]

	for row in sheet.iter_rows(min_row=2, max_col=16):  # up to column P
		cell_d = row[3]  # Column D
		cell_o = row[14]  # Column O
		cell_currency = row[15].value  # Get the value of column P

		# Ensure cell_d.value is a datetime before formatting
		if isinstance(cell_d.value, datetime):
			date_str = cell_d.value.strftime("%#m/%#d")  # Format to match 'today'

			if date_str == today:
				if cell_currency == "EURO":
					cell_o.value = EURO
				elif cell_currency == "USD":
					cell_o.value = USD
	wb.save("詢價單統計表_test.xlsx")



