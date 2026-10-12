import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load and look
df = pd.read_csv("supermarket_sales_case_study.csv")
rows_in = len(df)
print(df.shape)
df.head()
df.info()

# 2. Audit before you fix
print(df.isnull().sum())
audit = pd.DataFrame({
    "missing_count": df.isnull().sum(),
    "missing_percent": (df.isnull().mean() * 100).round(2),
})
print(audit[audit.missing_count > 0])
print("exact duplicate rows:", df.duplicated().sum())
print("duplicate invoice ids:", df.duplicated(subset=["Invoice ID"]).sum())
print(df["Gender"].unique())
print(df["Payment"].unique())

# 3. Drop exact duplicates
print("Before exact duplicate rows:", df.duplicated().sum())
df = df.drop_duplicates()
print("After cleaning exact duplicate rows:", df.duplicated().sum())
rows_step3 = len(df)

# 4. Resolve conflicting Invoice IDs
# The later row is a correction, so keep the last one
df = df.drop_duplicates(subset=["Invoice ID"], keep="last")
rows_step4 = len(df)

# 5. Standardise text columns
gender_map = {"male": "Male", "female": "Female"}
payment_map = {"cash": "Cash", "credit card": "Credit card", "ewallet": "Ewallet"}
df["Gender"] = df["Gender"].str.strip().str.lower().map(gender_map)
df["Payment"] = df["Payment"].str.strip().str.lower().map(payment_map)

# 6. Fix negative quantities
df["Quantity"] = df["Quantity"].abs()

# 7. Parse mixed dates
d1 = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
d2 = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
df["Date"] = d1.fillna(d2)

# 8. Check Total
calc_total = (df["Quantity"] * df["Unit price"] * 1.05).round(4)
diff = (df["Total"] - calc_total).abs()
df.loc[diff > 0.50, "Total"] = calc_total

# 9. Handle what is still missing
df["Customer type"] = df["Customer type"].fillna("Unknown")
df["Rating"] = df["Rating"].fillna(df["Rating"].median())
df = df.dropna(subset=["Date"])

# 10. Keep an audit trail
audit_trail = pd.DataFrame([
    {"step": "raw file loaded", "rows": rows_in, "removed": 0},
    {"step": "exact duplicates dropped", "rows": rows_step3, "removed": rows_in - rows_step3},
    {"step": "conflicting invoice ids resolved", "rows": rows_step4, "removed": rows_step3 - rows_step4},
    {"step": "missing dates dropped", "rows": len(df), "removed": rows_step4 - len(df)},
])
print(audit_trail)

# Brief 1: Add time columns
df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Quarter"] = df["Date"].dt.to_period("Q").astype(str)
df["Day of week"] = df["Date"].dt.day_name()
df["Hour"] = pd.to_datetime(df["Time"], format="%H:%M").dt.hour

# Brief 2: Bucket the trading day
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

# Brief 3: Compare against target
branch_qtr = df.groupby(["Branch", "Quarter"])["Total"].sum().reset_index()
branch_qtr.rename(columns={"Total": "Revenue"}, inplace=True)
branch_qtr["Target"] = 100000.0
branch_qtr["Variance"] = branch_qtr["Revenue"] - branch_qtr["Target"]
branch_qtr["% of target"] = (branch_qtr["Revenue"] / branch_qtr["Target"]) * 100
branch_qtr["Hit"] = branch_qtr["Revenue"] >= branch_qtr["Target"]
print(branch_qtr)

# Brief 4: Summarise each branch
branch_summary = branch_qtr.groupby("Branch").agg(
    avg_revenue=("Revenue", "mean"),
    quarters_hit=("Hit", "sum"),
    best_revenue=("Revenue", "max"),
    worst_revenue=("Revenue", "min"),
).reset_index()

rev_2023 = branch_qtr[branch_qtr["Quarter"].str.startswith("2023")].groupby("Branch")["Revenue"].sum()
rev_2024 = branch_qtr[branch_qtr["Quarter"].str.startswith("2024")].groupby("Branch")["Revenue"].sum()
branch_summary["YoY growth %"] = ((rev_2024.values / rev_2023.values) - 1) * 100
print(branch_summary)

# Brief 5: Find the busy times
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

# Brief 6: Chart, export, summarise
plt.figure(figsize=(10, 4))
sns.lineplot(data=branch_qtr, x="Quarter", y="Revenue", hue="Branch")
plt.axhline(100000, color="red", linestyle="--")
plt.title("Quarterly Revenue vs Target")
plt.show()

df.to_csv("outputs/supermarket_sales_clean.csv", index=False)

print("1. Total revenue is $2,402,106.66 across 8,514 transactions.")
print("2. Branch A has the highest average quarterly revenue ($103,798.63).")
print("3. Branch C has the highest YoY growth (+8.40%).")
print("4. Branch B had negative YoY growth (-5.26%).")
print("5. Peak busy times are weekends and 17:00-19:00.")
