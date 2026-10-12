# Parse mixed dates

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")

d1 = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
d2 = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
df["Date"] = d1.fillna(d2)

print("missing dates:", df["Date"].isna().sum())
```

# Output

```txt
missing dates: 62
```
