import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
print(df.shape)                
# df.head()   
# df.info() 
# print(df.isnull().sum())
# audit = pd.DataFrame({
#     "missing_count": df.isnull().sum(),
#     "missing_percent": (df.isnull().mean() * 100).round(2),
# })
# print(audit[audit.missing_count > 0])
# print("exact duplicate rows:", df.duplicated().sum())   
# print("Before exact duplicate rows:", df.duplicated().sum())   
print(df.drop_duplicates(subset=["Invoice ID"]))
# print("After cleaning exact duplicate rows:", df.duplicated().sum()) 
