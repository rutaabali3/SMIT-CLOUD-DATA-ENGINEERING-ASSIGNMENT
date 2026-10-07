# Audit before you fix: Finding Null Values

```py
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
print(df.shape)                
print(df.isnull().sum())
```

# Output

```txt
Invoice ID                  0
Branch                      0
City                        0
Customer type              64
Gender                      0
Product line                0
Unit price                  0
Quantity                    0
Tax 5%                      0
Total                       0
Date                       17
Time                        0
Payment                     0
cogs                        0
gross margin percentage     0
gross income                0
Rating                     88
dtype: int64
```