# Fix negative quantities

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")

print("Before:", (df["Quantity"] < 0).sum())
df["Quantity"] = df["Quantity"].abs()
print("After:", (df["Quantity"] < 0).sum())
```

# Output

```txt
Before: 57
After: 0
```
