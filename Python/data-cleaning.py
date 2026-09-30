import pandas as pd
import numpy as np

df = pd.read_csv("brewbuzz_raw_orders.csv")
print(df.shape)

#DATA QAULITY AUDIT

audit = pd.Dataframe({
    "missing_count": df.isnull().sum(),
    "missing_percent": (df.isnull().mean() * 100).round(2),
})
print(audit[audit.missing_count > 0])
print("Exact Duplicated Rows:" , df.duplicated().sum())