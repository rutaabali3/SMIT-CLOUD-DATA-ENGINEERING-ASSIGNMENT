# Bucket the trading day

```py
import pandas as pd
import numpy as np

conditions = [
    (df["Hour"] >= 10) & (df["Hour"] < 13),
    (df["Hour"] >= 13) & (df["Hour"] < 17),
    (df["Hour"] >= 17) & (df["Hour"] < 21),
]
choices = ["Morning", "Afternoon", "Evening"]
df["Bucket"] = np.select(conditions, choices, default="Other")

bucket_counts = df["Bucket"].value_counts()
hours = pd.Series({"Morning": 3, "Afternoon": 4, "Evening": 4})
txn_per_hour = bucket_counts / hours
print(txn_per_hour)
```

# Output

```txt
Evening      852.250000
Afternoon    738.250000
Morning      717.333333
dtype: float64
```
