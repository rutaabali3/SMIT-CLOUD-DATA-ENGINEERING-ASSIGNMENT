# Resolve conflicting Invoice IDs

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
df = df.drop_duplicates()

df = df.drop_duplicates(subset=["Invoice ID"], keep="last")
print(df.shape)
```

# Output

```txt
(8576, 17)
```
