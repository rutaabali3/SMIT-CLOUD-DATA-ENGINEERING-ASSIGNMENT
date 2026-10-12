# Add time columns

```py
import pandas as pd
import numpy as np

df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)
df["Day of week"] = df["Date"].dt.day_name()
df["Hour"] = pd.to_datetime(df["Time"], format="%H:%M").dt.hour

print(df[["Date", "Time", "Year", "Quarter", "Day of week", "Hour"]].head())
```

# Output

```txt
        Date   Time  Year Quarter Day of week  Hour
0 2023-01-01  12:46  2023  2023Q1      Sunday    12
1 2023-01-01  17:55  2023  2023Q1      Sunday    17
2 2023-01-01  12:40  2023  2023Q1      Sunday    12
3 2023-01-01  17:20  2023  2023Q1      Sunday    17
4 2023-01-01  17:36  2023  2023Q1      Sunday    17
```
