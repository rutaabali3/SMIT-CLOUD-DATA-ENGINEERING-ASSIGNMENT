# Check Total

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")
df["Quantity"] = df["Quantity"].abs()

calc_total = (df["Quantity"] * df["Unit price"] * 1.05).round(4)
diff = (df["Total"] - calc_total).abs()
print("off by > 0.50 before:", (diff > 0.50).sum())

df.loc[diff > 0.50, "Total"] = calc_total
diff_after = (df["Total"] - calc_total).abs()
print("off by > 0.50 after:", (diff_after > 0.50).sum())
```

# Output

```txt
off by > 0.50 before: 62
off by > 0.50 after: 0
```
