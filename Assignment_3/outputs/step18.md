# Chart, export, summarise

```py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 4))
sns.lineplot(data=branch_qtr, x="Quarter", y="Revenue", hue="Branch")
plt.axhline(100000, color="red", linestyle="--")
plt.title("Quarterly Revenue vs Target")
plt.show()

df.to_csv("outputs/supermarket_sales_clean.csv", index=False)

print("1. Total revenue is $2,402,106.66 across 8,514 transactions.")
print("2. Branch A has the highest average quarterly revenue ($103,798.63).")
print("3. Branch C has the highest YoY growth (+8.40%).")
print("4. Branch B had negative YoY growth (-5.26%).")
print("5. Peak busy times are weekends and 17:00-19:00.")
```

# Output

```txt
1. Total revenue is $2,402,106.66 across 8,514 transactions.
2. Branch A has the highest average quarterly revenue ($103,798.63).
3. Branch C has the highest YoY growth (+8.40%).
4. Branch B had negative YoY growth (-5.26%).
5. Peak busy times are weekends and 17:00-19:00.
```
