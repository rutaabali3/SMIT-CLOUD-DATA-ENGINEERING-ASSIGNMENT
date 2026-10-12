# Handle what is still missing

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")

d1 = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
d2 = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
df["Date"] = d1.fillna(d2)

df["Customer type"] = df["Customer type"].fillna("Unknown")
df["Rating"] = df["Rating"].fillna(df["Rating"].median())
df = df.dropna(subset=["Date"])

print(df.isnull().sum())
print("rows remaining:", len(df))
```

# Output

```txt
Invoice ID                 0
Branch                     0
City                       0
Customer type              0
Gender                     0
Product line               0
Unit price                 0
Quantity                   0
Tax 5%                     0
Total                      0
Date                       0
Time                       0
Payment                    0
cogs                       0
gross margin percentage    0
gross income               0
Rating                     0
dtype: int64
rows remaining: 8514
```
