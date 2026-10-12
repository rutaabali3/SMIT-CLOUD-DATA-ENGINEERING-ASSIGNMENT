# Load and look. Read the file and check how many rows and columns 

```python
import pandas as pd
import numpy as np

df = pd.read_csv("supermarket_sales_case_study.csv")
print(df.shape)                
df.head()  
```

# Output

```txt
ROWS: 8631 
COLUMN: 17
```