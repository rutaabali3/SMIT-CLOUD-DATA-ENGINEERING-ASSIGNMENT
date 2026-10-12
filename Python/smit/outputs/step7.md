# Standardise text columns

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")

gender_map = {"male": "Male", "female": "Female"}
payment_map = {"cash": "Cash", "credit card": "Credit card", "ewallet": "Ewallet"}

df["Gender"] = df["Gender"].str.strip().str.lower().map(gender_map)
df["Payment"] = df["Payment"].str.strip().str.lower().map(payment_map)

print(df["Gender"].unique())
print(df["Payment"].unique())
```

# Output

```txt
['Female' 'Male']
['Ewallet' 'Credit card' 'Cash']
```
