import pandas as pd
import sys


#內銷接單統計

def WIRE_SALE(START_DATE, END_DATE):
    data = pd.read_excel("WPC0430Q.xlsx")
    data["訂單日期"] = pd.to_datetime(data["訂單日期"])
    data.rename(columns={"Unnamed: 4": "客戶名稱"}, inplace=True)
    當周銷售訂單 = data[(data["訂單日期"] >= pd.to_datetime(START_DATE)) & (data["訂單日期"] <= pd.to_datetime(END_DATE))]
    當周銷售訂單 = 當周銷售訂單[["客戶名稱", "訂單重(Kgs)"]].copy().reset_index(drop=True)
    當周銷售訂單統計 = 當周銷售訂單.groupby("客戶名稱").sum()
    當周銷售訂單統計["Total"] = 當周銷售訂單["訂單重(Kgs)"].sum()
    
    return 當周銷售訂單統計, data  # Return the weekly sales statistics and the full data


def calculate_shipment(MONTH):
   
    data = pd.read_excel("WPC0430Q.xlsx")
    data.rename(columns={"Unnamed: 4": "客戶名稱"}, inplace=True)
    data["訂單交期"] = pd.to_datetime(data["訂單交期"])
    當月預估出貨量 = data[data["訂單交期"].dt.strftime('%Y/%m') == MONTH]  
    
    # Select relevant columns and reset the index
    當月預估出貨量 = 當月預估出貨量[["客戶名稱", "訂單重(Kgs)"]].copy().reset_index(drop=True)
    
    # Separate the data into two categories: 五金線 (Hardware Line) and 螺絲線 (Screw Line)
    五金線 = 當月預估出貨量[當月預估出貨量["客戶名稱"] == "雄台金屬"]
    螺絲線 = 當月預估出貨量[當月預估出貨量["客戶名稱"] != "雄台金屬"]
    
    # Calculate the total weight for each category in metric tons (MT)
    五金線統計 = 五金線["訂單重(Kgs)"].astype(float).sum() / 1000
    螺絲線統計 = 螺絲線["訂單重(Kgs)"].astype(float).sum() / 1000
    
    return 螺絲線統計, 五金線統計  # Return both shipment category statistics

def OEM_ORDER(START_DATE, END_DATE):
	
	data2 = pd.read_excel("ACM0130Q.xlsx")

	data2["代工日期"] = pd.to_datetime(data2["代工日期"]) 
	data2.rename(columns={"Unnamed: 4": "客戶名稱"}, inplace=True)
	當周代工訂單 = data2[(data2["代工日期"] >= START_DATE) & (data2["代工日期"] <= END_DATE)]
	當周代工訂單 = 當周代工訂單[["客戶名稱", "代工重(Kgs)"]].copy().reset_index(drop=True)
	當周代工訂單統計 = 當周代工訂單.groupby("客戶名稱").sum()
	當周代工訂單統計["Total"] = 當周代工訂單["代工重(Kgs)"].sum()

	return 當周代工訂單統計

def OEM_calculated_ship(MONTH):
	data2 = pd.read_excel("ACM0130Q.xlsx")
	data2.rename(columns={"Unnamed: 4": "客戶名稱"}, inplace=True)
	data2["訂單交期"] = pd.to_datetime(data2["訂單交期"])
	當月預估盤元量 = data2[data2["訂單交期"].dt.strftime('%Y/%m') == MONTH]
	當月預估盤元量 = 當月預估盤元量[["客戶名稱", "代工重(Kgs)", "原始線徑", "材質"]].copy().reset_index(drop=True)

	純代工預估統計 = 當月預估盤元量["代工重(Kgs)"].astype(float).sum() / 1000

	return 純代工預估統計

def OEM_SHIPPED():

	data3 = pd.read_excel("ASK4150B.xlsx")

	data3 = data3[["資料來源", "重量"]].copy().reset_index(drop=True)
	當月實際盤元量 = data3[data3["資料來源"] == "ACM0415M"]
	純代工實際統計 = 當月實際盤元量["重量"].astype(float).sum() / 1000

	return 純代工實際統計


#以下為外銷接單統計

def Screw_Order_List():
    data = pd.read_csv("0710Q.csv")
    data["Order_weight(MT)"] = data["接單重量(KGS)"].map(lambda x : float(x.replace(",","")))
    CHART_SOURCE = data[["客戶代號", "Order_weight(MT)"]].copy()
    ORDER_TABLE = CHART_SOURCE[["Order_weight(MT)", "客戶代號"]].groupby("客戶代號").sum()
    
    return ORDER_TABLE

def Monthly_Expect_Shipment():

    def TRAN_DATE(days) :
        DATE_LIST = days.split("/")
        if len(DATE_LIST[1]) < 2 :
            DATE_LIST[1] = "0" + DATE_LIST[1]
        return "{}/{}".format(DATE_LIST[0], DATE_LIST[1])

    data = pd.read_csv("0800Q.csv")
    data["Order_weight(MT)"] = data["訂單重量(KG)"].map(lambda x : float(x.replace(",",""))*0.001)
    CHART_SOURCE = data[["Order_weight(MT)", "訂單交期"]].copy()
    CHART_SOURCE["Order_Monthly"] = CHART_SOURCE["訂單交期"].apply(TRAN_DATE)
    EXCEPT_SHIP_TABLE = CHART_SOURCE[["Order_weight(MT)", "Order_Monthly"]].groupby("Order_Monthly").sum()
    
    return EXCEPT_SHIP_TABLE


if __name__ == "__main__":

    if len(sys.argv) > 1:  # Check if an argument is provided
        mode = sys.argv[1]
        
        if mode == "-SCREW":
            data_input = input("轉出 當周-0710Q 當年-0800Q")
            ORDER_TABLE = Screw_Order_List()
            print(f"\n訂單明細表:\n{ORDER_TABLE}")
            print(f"\nTOTAL_ORDER_WEIGHT : ",ORDER_TABLE["Order_weight(MT)"].sum())

            EXCEPT_SHIP_TABLE = Monthly_Expect_Shipment()
            print(f"\n\n每月預估出貨量\n{EXCEPT_SHIP_TABLE}")
            print(f"\nTOTAL_SHIPPING_WEIGHT : ",EXCEPT_SHIP_TABLE["Order_weight(MT)"].sum())

            print(f"\n\n實際出貨量至0810Q查看當月淨重")

        elif mode == "-WIRE":
            data_input = input("轉出 訂單交期當年-WPC0430Q.xlsx, ACM0130Q.xlsx 及 當月-ASK4150B.xlsx")
            date_input = input("輸入月份、起始日、結束日 (e.g., 2024/12 2024-12-16 2024-12-22): ")

            month123, ST_D, EN_D = date_input.split()

            當周銷售訂單統計, data = WIRE_SALE(ST_D, EN_D)
            print(f"\n當周銷售訂單統計:\n{當周銷售訂單統計}")

            螺絲線統計, 五金線統計 = calculate_shipment(month123)
            print(f"\n伸線預估出貨量:\n螺絲線 {螺絲線統計}MT \n次級品 {五金線統計}MT")

            print("\n伸線實際出貨量至WPC0810Q直接查看出貨重量")

            當周代工訂單統計 = OEM_ORDER(ST_D, EN_D)
            print(f"\n\n當周代工訂單統計:\n{當周代工訂單統計}")

            純代工預估統計 = OEM_calculated_ship(month123)
            print(f"\n代工預估出貨狀況: \n純代工 {純代工預估統計}MT")

            純代工實際統計 = OEM_SHIPPED()
            print(f"\n代工實際出貨量: \n純代工 {純代工實際統計}MT")

        else:
            print("Invalid argument. Use -SCREW for Screw Orders or -WIRE for Wire Sales.")
   


