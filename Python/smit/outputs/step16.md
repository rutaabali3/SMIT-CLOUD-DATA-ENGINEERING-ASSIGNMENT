# Summarise each branch

```py
import pandas as pd
import numpy as np

branch_summary = branch_qtr.groupby("Branch").agg(
    avg_revenue=("Revenue", "mean"),
    quarters_hit=("Hit", "sum"),
    best_revenue=("Revenue", "max"),
    worst_revenue=("Revenue", "min"),
).reset_index()

rev_2023 = branch_qtr[branch_qtr["Quarter"].str.startswith("2023")].groupby("Branch")["Revenue"].sum()
rev_2024 = branch_qtr[branch_qtr["Quarter"].str.startswith("2024")].groupby("Branch")["Revenue"].sum()
branch_summary["YoY growth %"] = ((rev_2024.values / rev_2023.values) - 1) * 100
print(branch_summary)
```

# Output

```txt
  Branch    avg_revenue  quarters_hit  best_revenue  worst_revenue  YoY growth %
0      A  103798.626750             4   129821.3280     89175.6705      1.056578
1      B   93167.815125             2   116106.4800     79174.1370     -5.264409
2      C  103296.888187             4   140298.6900     82013.9775      8.403525
```
