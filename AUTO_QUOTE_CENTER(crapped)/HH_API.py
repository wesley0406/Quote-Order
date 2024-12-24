import openai
import numpy as np 
import os
import pandas as pd

HH_PRICE = pd.read_excel(r"Z:\跨部門\螺絲報價\2 熱處理類別報價\螺絲熱處理牌價表-20231004-Gavin.xlsx")
print(HH_PRICE)