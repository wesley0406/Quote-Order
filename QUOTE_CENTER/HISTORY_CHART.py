import pandas as pd 
import os, re
import random 
import time
from datetime import datetime
import sqlite3
import plotly.graph_objs as go

class PRODCUT_CATEGORY_CHART : 
	def __init__(self,):

		self.DATABASE = r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\QUOTATION_DATABASE.db"
		self.CUSTOMER_CODE = input("Please enter the Customer ID :").strip()
		self.ALL_ITEM = dict()
		self.RUN_PROCEDURE()
		

	def RUN_PROCEDURE(self,):
		#enter the customer you would like to analyze
		print("Welcome to the Customer Product Analysis App!")
		#customer_id = input("Please enter the Customer ID :").strip()
		self.ALL_ITEM = self.SEARCH_BY_CATEGORY(self.CUSTOMER_CODE)

		if not self.ALL_ITEM:
			print(f"No data found for customer code: {self.CUSTOMER_CODE}")

		else :
			print("Please choose a category from below list : ")
			for cate in self.ALL_ITEM :
				print(cate)
			choosed_cate = input("Enter the category you want :").strip()
			if choosed_cate not in self.ALL_ITEM :
				print("Please choose the correct cateogy, thanks ")
			else :
				self.DRAW_PROFIT_CHART_3D(self.HISTORY_PROFIT(self.ALL_ITEM[choosed_cate])).show()

	def FORMATTED_TITLE(self, title): # split the name of the product if the length is more than 70
		# Find the index of the closest space to the 70th character
		split_index   =   title[:70].rfind(' ')
		if split_index   ==   -1:
			split_index   =   70
		# Split the string at the closest space index
		first_line   =   title[:split_index]
		second_line   =   title[split_index:].strip()  # Remove leading/trailing spaces if any

		# Combine the lines with a line break <br>
		formatted_title   =   first_line + "<br>" + second_line
		return formatted_title

	def DRAW_PROFIT_CHART(self, INPUT_DF):

		fig   =   go.Figure()

		# Ensure QUOTE_DATE is in datetime format
		INPUT_DF['QUOTE_DATE']   =   pd.to_datetime(INPUT_DF['QUOTE_DATE'])

		# Add traces for each unique product code
		for code in INPUT_DF["PRODUCT_CODE"].unique():
			# Filter and sort data for the current product code
			table   =   INPUT_DF[INPUT_DF["PRODUCT_CODE"]   ==   code].sort_values(by  =  "QUOTE_DATE")
			
			# Extract custom data
			refresh_variable   =   table[['WIRE_PRICE', 'PROFIT_RATE', 'EXCHANGE_RATE']].values

			# Add trace for the current product code
			fig.add_trace(go.Scatter(
				x   =   table['QUOTE_DATE'],
				y   =   table['PROFIT_RATE'],
				mode   =   'lines+markers',
				marker   =   dict(size  =  8),
				name   =   code,
				customdata   =   refresh_variable,  # Set custom data here
				hovertemplate   =   "<br>".join([
					"報價日期: %{x}",
					"價格: %{y}",
					"線材: %{customdata[0]}",  # WIRE_PRICE
					"利潤: %{customdata[1]}",  # PROFIT_RATE
					"匯率: %{customdata[2]}",  # EXCHANGE_RATE
				])
			))

		# Update layout once, outside the loop
		fig.update_layout(
			title   =   dict(text   =   "Profit Rate Chart"),  # Replace with your FORMATTED_TITLE function if needed
			title_font   =   dict(size   =   15),
			xaxis_title   =   'Date',
			yaxis_title   =   'Profit rate',
			hovermode   =   "x",
			plot_bgcolor   =   'rgba(135, 206, 250, 0.3)',
			hoverlabel   =   dict(bordercolor  =  "rgba(135, 206, 250, 0.7)"),
			yaxis2   =   dict(
				title   =   'Product Code',
				side   =   'right',
				overlaying   =   'y',
				tickvals   =   list(range(len(INPUT_DF["PRODUCT_CODE"].unique()))),
				ticktext   =   INPUT_DF["PRODUCT_CODE"].unique().astype(str).tolist(),
			)
		)
		return fig

	def HISTORY_PROFIT(self, matching) :
		with sqlite3.connect(self.DATABASE) as connection :
			placeholders   =   ', '.join(['?'] * len(matching))
			query   =   f"SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE PRODUCT_CODE IN ({placeholders})"
			df   =   pd.read_sql_query(query, connection, params   =   matching)
		return df

	def DRAW_PROFIT_CHART_3D(self, INPUT_DF):
		fig  =  go.Figure()

		# Convert QUOTE_DATE to datetime
		INPUT_DF['QUOTE_DATE']  =  pd.to_datetime(INPUT_DF['QUOTE_DATE'])

		# Add traces for each PRODUCT_CODE
		for code in INPUT_DF["PRODUCT_CODE"].unique():
			# Filter and sort data for the current product code
			table  =  INPUT_DF[INPUT_DF["PRODUCT_CODE"]  ==  code].sort_values(by = "QUOTE_DATE")

			# Extract custom data
			refresh_variable  =  table[['WIRE_PRICE', 'PROFIT_RATE',  'EXCHANGE_RATE', 'TOTAL_PRICE_M']].values

			# Add trace for the current product code
			fig.add_trace(go.Scatter3d(
				x = table['QUOTE_DATE'],
				y = table['WIRE_PRICE'],
				z = table['TOTAL_PRICE_M'],
				mode = 'lines+markers',
				marker = dict(
					size = 10,
					color  =  "rgb({}, {}, {})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),  # Assign a unique color for each product code
					opacity = 0.8
				),
				name = code,
				customdata = refresh_variable,  # Set custom data here
				hovertemplate = "<br>".join([
					"報價日期: %{x}",
					"線材: %{y}",			  # WIRE_PRICE
					"利潤: %{customdata[1]}",  # PROFIT_RATE
					"匯率: %{customdata[2]}",  # PROFIT_RATE
					"總價: %{customdata[3]}",  # EXCHANGE_RATE
				])
			))

		# Update layout
		fig.update_layout(
			scene = dict(
				xaxis_title = 'Quote Date (Days)',
				yaxis = dict(
					title = "Wire Price",
					autorange = "reversed"),
				zaxis_title = 'Price/M',
			),
			title = "3D Visualization of Product Data",
		)

		return fig

	# split the  item code into different category
	def MATCH_CATEGORY(self, code):

		if not code :
			return {
				"Prefix" : None,
				"Number" : None,
				"Suffix" : None,
				"Modifier" : None
			}

		# Split by the delimiter, if it exists for C019
		if len(code) > 15 :
			main_part = str(code)[:6]
			#additional_part = '.'.join(parts[2:]) if len(parts) > 2 else None
			return {
				"Prefix" : main_part,
				"Number" : str(code)[7:11],
				"Suffix" : str(code)[12:],
				"Modifier" : None
			}
		else : 
			# Use regex to extract components
			match = re.match(r'([A-Z]+)(\d+)([A-Z]*)(?:-(\d+))?', code)
			if match:
				prefix, number, suffix, modifier = match.groups()
				return {
					'Prefix': prefix,
					'Number': str(number),
					'Suffix': suffix if suffix else None,
					'Modifier': int(modifier) if modifier else None
				}
			else:
				return {'Prefix': None, 'Number': None, 'Suffix': None, 'Modifier': None}

	# search the category through customer code 
	def SEARCH_BY_CATEGORY(self, customer_id) :

		connection = sqlite3.connect(self.DATABASE)
		CDS = dict()																   #CATERORIZE DATA STRUCTURE
		df = pd.read_sql_query("SELECT * FROM CUSTOMER_PRODUCT_SUMMARY WHERE CUSTOMER_CODE = ?", connection, params = (customer_id,))
		connection.close()
		categorized_data = df["PRODUCT_CODE"].apply(self.MATCH_CATEGORY).apply(pd.Series)   # anatamize the item code 
		df = pd.concat([df, categorized_data], axis = 1)							   # glue up the new column with old one
		for product_cate in df["Prefix"].unique():									 # categorize by the couple first English letter 
			seperate_cate = df[df["Prefix"] == product_cate]
			CDS[product_cate] = [i for i in seperate_cate["PRODUCT_CODE"].unique()]

		return CDS

# Run the app
if __name__ == "__main__":
	PRODCUT_CATEGORY_CHART()
