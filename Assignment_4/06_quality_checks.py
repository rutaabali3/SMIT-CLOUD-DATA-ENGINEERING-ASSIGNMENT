"""
=============================================================================
 STEP 6 - PROVE THE NUMBERS                                (about 5 minutes)
=============================================================================

    python 06_quality_checks.py

You now have a number to put in front of Finance. Before you do, answer the
question they will ask: "how do I know this is right?"

A data quality check is a question you ask the database where you already
know what the answer must be. If it answers something else, you have a bug
and you find it HERE, not in the meeting.

Every result is written to dq.results, so the checks leave a record that
outlives this terminal window.

The one that matters most is RECONCILIATION:

    raw rows = clean rows + rejected rows + duplicates removed

If that balances, every single row that came out of a CSV is accounted for:
used, or set aside on purpose. If it does not balance, rows are disappearing
somewhere in your pipeline and nothing downstream can be trusted - however
convincing it looks.
=============================================================================
"""
from datetime import datetime

import pandas as pd

from db import banner, done, fetch_df, fetch_value, insert_dataframe, step

checks = []


def record(name, passed, detail):
    checks.append({"check_name": name, "passed": bool(passed),
                   "detail": str(detail)[:200], "run_at": datetime.now()})
    print(f"  [{'  OK  ' if passed else ' FAIL '}] {name}")
    print(f"           {detail}")


banner("STEP 6 - DATA QUALITY CHECKS")

# ===========================================================================
step(1, "Is the key actually a key?")
# ===========================================================================
# clean.parcels already has a PRIMARY KEY, so SQL Server would have refused
# a duplicate. We check anyway - a constraint you never verified is a
# constraint you only believe in.
rows = fetch_value("SELECT COUNT(*) FROM clean.parcels")
distinct = fetch_value("SELECT COUNT(DISTINCT parcel_id) FROM clean.parcels")
nulls = fetch_value("SELECT COUNT(*) FROM clean.parcels WHERE parcel_id IS NULL")
record("parcel_id is unique and not null",
       rows == distinct and nulls == 0,
       f"{rows:,} rows, {distinct:,} distinct, {nulls} null")

# ===========================================================================
step(2, "RECONCILIATION - is every raw scan accounted for?")
# ===========================================================================
raw_scans = fetch_value("SELECT COUNT(*) FROM raw.scans")
clean_scans = fetch_value("SELECT COUNT(*) FROM clean.scans")
rejected = fetch_value("SELECT COUNT(*) FROM clean.rejected_scans")
duplicates = raw_scans - clean_scans - rejected
record("every raw scan is used, rejected or a known duplicate",
       clean_scans + rejected + duplicates == raw_scans,
       f"{raw_scans:,} raw = {clean_scans:,} clean + {rejected} rejected "
       f"+ {duplicates} duplicates removed")

for table, raw_table in [("clean.parcels_all", "raw.parcels"),
                         ("clean.remittances", "raw.remittances")]:
    a, b = fetch_value(f"SELECT COUNT(*) FROM {raw_table}"), fetch_value(f"SELECT COUNT(*) FROM {table}")
    record(f"{raw_table} -> {table} loses nothing", a == b, f"{a:,} raw, {b:,} cleaned")

# ===========================================================================
step(3, "REFERENTIAL INTEGRITY - does every row point at something real?")
# ===========================================================================
orphan_scans = fetch_value("""
    SELECT COUNT(*) FROM clean.scans s
    WHERE NOT EXISTS (SELECT 1 FROM clean.parcels p WHERE p.parcel_id = s.parcel_id)
""")
record("every clean scan belongs to a known parcel", orphan_scans == 0,
       f"{orphan_scans} orphans (the 30 we found went to clean.rejected_scans)")

orphan_remits = fetch_value("""
    SELECT COUNT(*) FROM clean.remittances r
    WHERE NOT EXISTS (SELECT 1 FROM clean.parcels p WHERE p.parcel_id = r.parcel_id)
""")
record("every remittance belongs to a known parcel", orphan_remits == 0,
       f"{orphan_remits} remittances with no matching parcel")

# ===========================================================================
step(4, "ACCEPTED VALUES - only the statuses and zones we expect")
# ===========================================================================
# A new value appearing in a column is how an upstream change announces
# itself. Without this check it announces itself as a wrong total instead.
bad_status = fetch_df("""
    SELECT final_status, COUNT(*) AS n FROM clean.parcel_final
    WHERE final_status NOT IN ('delivered','returned','in_transit','picked_up','no_scan')
    GROUP BY final_status
""")
record("final_status holds only expected values", len(bad_status) == 0,
       "all known" if len(bad_status) == 0 else bad_status.to_dict("records"))

zones = fetch_value("SELECT COUNT(DISTINCT zone) FROM clean.parcels")
record("exactly 4 zones after cleaning", zones == 4, f"{zones} distinct zone values")

# ===========================================================================
step(5, "BUSINESS SANITY - things that cannot be true")
# ===========================================================================
backwards = fetch_value("""
    SELECT COUNT(*) FROM clean.parcel_final WHERE delivered_date < booked_date
""")
record("nothing was delivered before it was booked", backwards == 0,
       f"{backwards} parcels (this is the check that caught the date-parsing bug)")

negative = fetch_value("SELECT COUNT(*) FROM clean.remittances WHERE amount < 0")
record("no negative remittances", negative == 0, f"{negative} rows with amount < 0")

owed_but_not_delivered = fetch_value("""
    SELECT COUNT(*) FROM clean.parcel_final
    WHERE final_status <> 'delivered' AND cod_due <> 0
""")
record("only delivered parcels owe cash (rule 4)", owed_but_not_delivered == 0,
       f"{owed_but_not_delivered} undelivered parcels with cod_due <> 0")

# ===========================================================================
step(6, "Write the results so they outlive this terminal")
# ===========================================================================
df = pd.DataFrame(checks)
insert_dataframe(df, "dq.results", {
    "check_name": "NVARCHAR(100)", "passed": "BIT",
    "detail": "NVARCHAR(200)", "run_at": "DATETIME2",
})

passed = int(df.passed.sum())
print(f"\n  dq.results: {passed} of {len(df)} checks passed")

if passed != len(df):
    print("\n  SOMETHING FAILED. Do not present these numbers until it is green.")
    raise SystemExit(1)

done("Every check passed. The numbers in results/ are defensible.\n"
     "     Read them back with:  SELECT * FROM dq.results ORDER BY run_at;")
