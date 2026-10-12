# Audit before you fix: Removing Duplicate Values

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
print(df.shape)                
print("Before exact duplicate rows:", df.duplicated().sum())   
df = df.drop_duplicates()
print("After cleaning exact duplicate rows:", df.duplicated().sum()) 
```

# Output

```txt
Before exact duplicate rows: 30
After cleaning exact duplicate rows: 0
```