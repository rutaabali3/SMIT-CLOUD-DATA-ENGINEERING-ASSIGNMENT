"""
=============================================================================
 STEP 1 - LOOK AT THE FILES BEFORE YOU TOUCH THEM          (about 5 minutes)
=============================================================================

    python 01_profile_the_data.py

Nothing here writes to the database. This step exists because the single
most expensive mistake in data work is cleaning something you never looked
at, then discovering at the end that your assumption was wrong.

Five minutes here saves twenty later. Read the output and find, with your
own eyes, the five problems the brief warns you about:

    1. parcels.csv has MORE rows than it has distinct parcel_ids
    2. booked_date is written three different ways
    3. zone is written in mixed case, sometimes with stray spaces
    4. amount in cod_remittances.csv is TEXT - "Rs 1,250", not 1250
    5. some scans point at parcel_ids that are not in parcels.csv

Do not fix anything yet. Just see it.
=============================================================================
"""
import pandas as pd

from config import DATA_DIR
from db import banner, done, step

pd.set_option("display.width", 100)
pd.set_option("display.max_columns", 20)


def read_as_text(name):
    """
    dtype=str             -> never let pandas guess a type for us
    keep_default_na=False -> an empty cell stays "", it does not become NaN

    We want to see the data as it actually is on disk, not as pandas
    wishes it were.
    """
    return pd.read_csv(DATA_DIR / name, dtype=str, keep_default_na=False)


banner("STEP 1 - PROFILING THE RAW FILES")
print(f"  reading from: {DATA_DIR}")

parcels = read_as_text("parcels.csv")
scans = read_as_text("scans.csv")
remits = read_as_text("cod_remittances.csv")

# ---------------------------------------------------------------------------
step(1, "How big is each file, and what is in it?")
# ---------------------------------------------------------------------------
for name, df in [("parcels", parcels), ("scans", scans), ("remittances", remits)]:
    print(f"\n  {name}: {len(df):,} rows x {len(df.columns)} columns")
    print(f"    columns: {', '.join(df.columns)}")
    print(df.head(3).to_string(index=False, max_colwidth=22))

# ---------------------------------------------------------------------------
step(2, "PROBLEM 1 - duplicate parcels")
# ---------------------------------------------------------------------------
# len() counts rows. nunique() counts distinct values. When those two numbers
# disagree on a column that is supposed to be the key, you have duplicates.
total, distinct = len(parcels), parcels.parcel_id.nunique()
print(f"\n  rows: {total:,}   distinct parcel_id: {distinct:,}   duplicates: {total - distinct}")

repeated = parcels[parcels.parcel_id.duplicated(keep=False)].sort_values(["parcel_id", "updated_at"])
print("\n  the same parcel, twice - note which row has the later updated_at:")
print(repeated.head(4).to_string(index=False, max_colwidth=20))

# ---------------------------------------------------------------------------
step(3, "PROBLEM 2 - three date formats in one column")
# ---------------------------------------------------------------------------
# A date is only a date once it is TYPED. Until then it is a string, and
# three systems wrote these strings three different ways.
def shape_of(value):
    """Turn '20/09/2026' into '99/99/9999' so we can count the SHAPES."""
    return "".join("9" if c.isdigit() else ("A" if c.isalpha() else c) for c in value)


print("\n  booked_date, by shape:")
print(parcels.booked_date.map(shape_of).value_counts().to_string())
print("\n  examples:")
for shape, group in parcels.groupby(parcels.booked_date.map(shape_of)):
    print(f"    {shape:<12} e.g. {group.booked_date.iloc[0]}")

# ---------------------------------------------------------------------------
step(4, "PROBLEM 3 - zone names that do not match each other")
# ---------------------------------------------------------------------------
# There are only four zones. value_counts() says otherwise, and every extra
# line here is a row that would fall out of a GROUP BY.
print(f"\n  distinct zone values as stored: {parcels.zone.nunique()}")
print(parcels.zone.value_counts().head(12).to_string())
print(f"\n  after trimming spaces and fixing case: {parcels.zone.str.strip().str.title().nunique()}")
print(f"    -> {sorted(parcels.zone.str.strip().str.title().unique())}")

# ---------------------------------------------------------------------------
step(5, "PROBLEM 4 - money stored as text")
# ---------------------------------------------------------------------------
print("\n  amount, as delivered:")
print(remits.amount.head(6).to_string(index=False))
print("\n  you cannot SUM any of these until the Rs, the commas and the")
print("  spaces are gone. pd.to_numeric would turn every one of them into NaN.")

# ---------------------------------------------------------------------------
step(6, "PROBLEM 5 - scans for parcels that do not exist")
# ---------------------------------------------------------------------------
known = set(parcels.parcel_id)
orphans = scans[~scans.parcel_id.isin(known)]
print(f"\n  scans: {len(scans):,}   of those, pointing at an unknown parcel: {len(orphans)}")
print(f"  examples: {', '.join(orphans.parcel_id.head(5))}")
print("\n  These are NOT rubbish to delete quietly. In step 3 they go into")
print("  clean.rejected_scans with a reason, so every raw row is accounted for.")

# ---------------------------------------------------------------------------
step(7, "And a look at the scan statuses")
# ---------------------------------------------------------------------------
print()
print(scans.status.value_counts().to_string())
print("\n  'delivered' and 'returned' are both ENDINGS. A parcel whose last")
print("  scan is 'in_transit' never finished - and owes no cash.")

done("Nothing was written. You now know what you are dealing with.\n"
     "     Next:  python 02_load_raw.py")
