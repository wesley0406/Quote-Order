import pandas as pd 

#將2023 李國忠的車趟轉為excel 檔案

with pd.ExcelFile("CLEAN_DATA.xlsx") as MOTHER:
	ROUGH = pd.read_excel(MOTHER, "ROUTE2024")
	ROUGH["DATE"] = pd.to_datetime(ROUGH["DATE"]).dt.date
	ROUGH["ORDER_CODE"] = ROUGH["DATE"].astype(str) + "-" + ROUGH["DRIVES"].astype(str)
	for date in ROUGH["ORDER_CODE"].unique() :
		print(date)
		df_date = ROUGH.loc[ROUGH['ORDER_CODE'] == date, ["FACTORY_CODE", "KGS"]]
		df_date['KGS'] = df_date["KGS"][::-1].cumsum()[::-1]   # 調整每載重為第一趟是總和然後逐次減掉
		output_filename = f'2024_CAR_TRACK/{date}.xlsx'   
		df_date.to_excel(output_filename, index=False)         # 寫入檔案
		print(f"Data for {date} saved to {output_filename}")

	