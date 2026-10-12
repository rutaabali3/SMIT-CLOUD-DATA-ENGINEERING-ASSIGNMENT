# Compare against target

```py
import pandas as pd
import numpy as np

branch_qtr = df.groupby(["Branch", "Quarter"])["Total"].sum().reset_index()
branch_qtr.rename(columns={"Total": "Revenue"}, inplace=True)
branch_qtr["Target"] = 100000.0
branch_qtr["Variance"] = branch_qtr["Revenue"] - branch_qtr["Target"]
branch_qtr["% of target"] = (branch_qtr["Revenue"] / branch_qtr["Target"]) * 100
branch_qtr["Hit"] = branch_qtr["Revenue"] >= branch_qtr["Target"]
print(branch_qtr.head(6))
```

# Output

```txt
  Branch Quarter      Revenue    Target    Variance  % of target    Hit
0      A  2023Q1  102248.7795  100000.0   2248.7795   102.248779   True
1      A  2023Q2   90064.1595  100000.0  -9935.8405    90.064160  False
2      A  2023Q3   90878.3400  100000.0  -9121.6600    90.878340  False
3      A  2023Q4  129821.3280  100000.0  29821.3280   129.821328   True
4      A  2024Q1  112450.6425  100000.0  12450.6425   112.450643   True
5      A  2024Q2   98243.2815  100000.0  -1756.7185    98.243282  False
```
