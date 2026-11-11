"""
=============================================================================
 STEP 2 - LOAD THE FILES INTO SQL SERVER, UNCHANGED        (about 5 minutes)
=============================================================================

    python 02_load_raw.py

This step is deliberately boring. Its only job is to get the three files
into the database EXACTLY as delivered, and prove nothing was lost on the
way in.

Three rules, and the reason for each:

  1. EVERY COLUMN IS TEXT (NVARCHAR).
     You saw in step 1 that booked_date holds three different formats. Ask
     SQL Server to store that as a DATE now and it rejects rows or mangles
     them. Raw means raw. Typing happens in step 3.

  2. WE ADD THREE TRACKING COLUMNS to every table:
        _source_file   which file this row came from
        _loaded_at     when we loaded it
        _row_hash      a fingerprint of the row's original values
     Six months from now somebody will ask "where did this row come from?"
     These columns answer it.

  3. RUNNING IT TWICE MUST NOT DOUBLE THE ROWS.
     That property is called IDEMPOTENCE. We get it the blunt way: drop the
     table, recreate it, refill it. For 6,000 rows that is the right call -
     it is one line, it cannot drift, and somebody always runs a script
     twice. At a billion rows you would need a smarter answer.
=============================================================================
"""
import hashlib
from datetime import datetime

import pandas as pd

from config import DATA_DIR, SQL_DATABASE
from db import banner, done, get_connection, insert_dataframe, run_sql, step, table_count

FILES = [
    ("parcels.csv",         "raw.parcels"),
    ("scans.csv",           "raw.scans"),
    ("cod_remittances.csv", "raw.remittances"),
]


def read_as_text(path):
    """Same two arguments as step 1, for the same two reasons."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def add_tracking_columns(df, filename):
    """
    _row_hash is a fingerprint: feed the row's values to MD5 and you get a
    short string that changes if ANY value in the row changes. It is how you
    later answer "is this the same row I loaded last week, or an edited one?"

    MD5 is used here as a checksum, not as security. Never use it for passwords.
    """
    joined = df.astype(str).agg("|".join, axis=1)
    df = df.copy()
    df["_source_file"] = filename
    df["_loaded_at"] = datetime.now()
    df["_row_hash"] = joined.map(lambda row: hashlib.md5(row.encode()).hexdigest())
    return df


banner("STEP 2 - LOADING THE RAW FILES INTO SQL SERVER")
print(f"  database: {SQL_DATABASE}")
print(f"  reading from: {DATA_DIR}")

# ---------------------------------------------------------------------------
step(1, "Make sure the 'raw' schema exists")
# ---------------------------------------------------------------------------
# A SCHEMA is a folder inside a database. Putting the untouched copies in
# `raw` and the cleaned ones in `clean` means you can always tell, from the
# table name alone, whether you are looking at evidence or at a conclusion.
for schema in ("raw", "clean", "dq"):
    run_sql(f"IF SCHEMA_ID('{schema}') IS NULL EXEC('CREATE SCHEMA {schema}');")
print("\n  schemas ready: raw, clean, dq")

# ---------------------------------------------------------------------------
step(2, "Load each file")
# ---------------------------------------------------------------------------
counts = []
for filename, table in FILES:
    df = read_as_text(DATA_DIR / filename)
    rows_in_file = len(df)

    df = add_tracking_columns(df, filename)

    # NVARCHAR(200) for every original column. Wide enough for anything in
    # these files, and narrow enough that a 500-character surprise fails
    # loudly instead of being silently stored.
    column_types = {c: "NVARCHAR(200)" for c in df.columns}
    column_types["_loaded_at"] = "DATETIME2"
    column_types["_row_hash"] = "CHAR(32)"

    rows_written = insert_dataframe(df, table, column_types)
    counts.append((filename, table, rows_in_file, rows_written))
    print(f"  {filename:<22} -> {table:<18} {rows_written:>6,} rows")

# ---------------------------------------------------------------------------
step(3, "RECONCILE - does the database hold what the files held?")
# ---------------------------------------------------------------------------
# This is the whole reason the step exists. A load you have not reconciled
# is a load you are only assuming worked.
print()
print(f"  {'file':<22} {'in file':>9} {'in table':>10}   match")
all_match = True
for filename, table, rows_in_file, _ in counts:
    in_table = table_count(table)
    ok = in_table == rows_in_file
    all_match &= ok
    print(f"  {filename:<22} {rows_in_file:>9,} {in_table:>10,}   {'yes' if ok else 'NO'}")

if not all_match:
    raise SystemExit("\n  ROW COUNTS DO NOT MATCH. Stop and find out why before going on.")

done("Every row in every file is now in SQL Server, untouched.\n"
     "     Run this script again if you like - the counts will not change.\n"
     "     Next:  python 03_clean_tables.py")
