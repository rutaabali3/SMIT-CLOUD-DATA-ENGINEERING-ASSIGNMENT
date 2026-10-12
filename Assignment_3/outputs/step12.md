# Keep an audit trail

```py
import pandas as pd
import numpy as np

audit_trail = pd.DataFrame([
    {"step": "raw file loaded", "rows": rows_in, "removed": 0},
    {"step": "exact duplicates dropped", "rows": rows_step3, "removed": rows_in - rows_step3},
    {"step": "conflicting invoice ids resolved", "rows": rows_step4, "removed": rows_step3 - rows_step4},
    {"step": "missing dates dropped", "rows": len(df), "removed": rows_step4 - len(df)},
])
print(audit_trail)
```

# Output

```txt
                               step  rows  removed
0                   raw file loaded  8631        0
1          exact duplicates dropped  8601       30
2  conflicting invoice ids resolved  8576       25
3             missing dates dropped  8514       62
```
