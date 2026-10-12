# Find the busy times

```py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

dow_counts = df["Day of week"].value_counts()
dow_days = df.groupby("Day of week")["Date"].nunique()
avg_per_day = dow_counts / dow_days
print(avg_per_day)

heat_data = df.pivot_table(index="Day of week", columns="Hour", values="Invoice ID", aggfunc="count")
heat_avg = heat_data.div(dow_days, axis=0)

plt.figure(figsize=(10, 4))
sns.heatmap(heat_avg, cmap="YlOrRd")
plt.title("Busy Times by Day and Hour")
plt.show()
```

# Output

```txt
Friday       12.708738
Monday        9.278846
Saturday     15.725490
Sunday       14.417476
Thursday     10.388350
Tuesday       9.807692
Wednesday    10.201923
dtype: float64
```
