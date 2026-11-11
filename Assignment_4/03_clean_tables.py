"""
=============================================================================
 STEP 3 - CLEAN THE THREE TABLES                          (about 15 minutes)
=============================================================================

    python 03_clean_tables.py

Now we fix the five problems step 1 showed us, and we fix every one of them
IN CODE. Nobody opens a CSV and edits it by hand - do that and your result
can never be rebuilt, reviewed, or trusted.

What this step produces:

    clean.parcels          one row per parcel, real DATE and DECIMAL types
    clean.merge_log        which duplicate rows we dropped, and why
    clean.scans            duplicate scans removed
    clean.rejected_scans   scans we could NOT use, each with a reason
    clean.remittances      amount as a number you can SUM

Where the work happens, and why:

    PANDAS does the parsing - three date formats, "Rs 1,250" -> 1250.00.
    Python is simply better at messy strings than T-SQL is.

    SQL SERVER does the set logic - "which row wins", "is this scan a
    duplicate of the one before it". Those are window functions, and
    window functions are what a database is for.

Use each tool for what it is good at. That choice IS the lesson.
=============================================================================
"""
import pandas as pd

from db import (banner, done, fetch_df, insert_dataframe, run_sql, step,
                table_count)


#: The three ways these files write a date. Order matters only in that we
#: try each one and keep whatever parses.
DATE_FORMATS = [
    "%Y-%m-%d",     # 2026-09-21   ISO
    "%d/%m/%Y",     # 21/09/2026   day first, slashes
    "%d-%b-%Y",     # 21-Sep-2026  day first, month name
]


def to_date(series):
    """
    Parse all three formats WITHOUT letting pandas guess.

    DO NOT use pd.to_datetime(series, format="mixed", dayfirst=True) here.
    It looks like the tidy one-liner and it is wrong: on this data it reads
    "11/09/2026" as 9 November instead of 11 September. Nothing crashes,
    nothing warns - you just get a parcel delivered two months before it was
    booked, and you only find out if you check.

    THAT is the lesson. A date like 04/09/2026 is genuinely ambiguous, and
    the only safe answer is to say which format you mean rather than hope the
    library agrees with you.

    So: try each known format in turn, and let each value be claimed by the
    first one that fits. 2026-09-21 cannot parse as %d/%m/%Y, 21/09/2026
    cannot parse as %Y-%m-%d, and so on - the formats do not overlap, so
    there is nothing left to guess.

    errors="coerce" turns anything unparseable into NaT (missing) instead of
    crashing. We count those afterwards - a silent NaT nobody counted is how
    wrong numbers get shipped.
    """
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        still_missing = parsed.isna()
        if not still_missing.any():
            break
        parsed.loc[still_missing] = pd.to_datetime(
            series[still_missing], format=fmt, errors="coerce")
    return parsed


def to_money(series):
    r"""
    "Rs 1,250" -> 1250.0

    The regex [^\d.] means "any character that is not a digit and not a dot".
    We delete all of those, then convert what is left. That one line handles
    the Rs prefix, the thousands commas and the padding spaces together.
    """
    stripped = series.str.replace(r"[^\d.]", "", regex=True)
    return pd.to_numeric(stripped, errors="coerce")


banner("STEP 3 - CLEANING")

# ===========================================================================
step(1, "PARCELS - parse the types, normalise the zones")
# ===========================================================================
parcels = fetch_df("""
    SELECT parcel_id, booked_date, promised_date, zone, rider_id,
           cod_amount, updated_at
    FROM raw.parcels
""")

parcels["booked_date"] = to_date(parcels.booked_date).dt.date
parcels["promised_date"] = to_date(parcels.promised_date).dt.date
parcels["updated_at"] = pd.to_datetime(parcels.updated_at, errors="coerce")
parcels["cod_amount"] = pd.to_numeric(parcels.cod_amount, errors="coerce")

# .strip() kills the stray spaces, .title() makes "korangi" and "KORANGI"
# into the same "Korangi". Four zones again, as they always should have been.
parcels["zone"] = parcels.zone.str.strip().str.title()
parcels["rider_id"] = parcels.rider_id.str.strip().str.upper()

unparsed = parcels.booked_date.isna().sum()
print(f"\n  dates parsed, {unparsed} unparseable")
print(f"  zones now: {sorted(parcels.zone.unique())}")

insert_dataframe(parcels, "clean.parcels_all", {
    "parcel_id": "NVARCHAR(20)", "booked_date": "DATE", "promised_date": "DATE",
    "zone": "NVARCHAR(50)", "rider_id": "NVARCHAR(10)",
    "cod_amount": "DECIMAL(10,2)", "updated_at": "DATETIME2",
})

# ===========================================================================
step(2, "PARCELS - the duplicates: keep the latest updated_at")
# ===========================================================================
# ROW_NUMBER() hands every row a position inside its own group. Here the
# group is one parcel_id, and the order is newest-first - so rn = 1 is the
# row we keep and everything else is a superseded older copy.
#
# We write the losers to clean.merge_log instead of deleting them silently.
# "We dropped 40 rows" is an answer. "We dropped 40 rows, here they are,
# here is why" is evidence.
run_sql("IF OBJECT_ID('clean.parcels','U') IS NOT NULL DROP TABLE clean.parcels;")
run_sql("IF OBJECT_ID('clean.merge_log','U') IS NOT NULL DROP TABLE clean.merge_log;")
run_sql("""
    WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY parcel_id
                                     ORDER BY updated_at DESC) AS rn
        FROM clean.parcels_all
    )
    SELECT parcel_id, booked_date, promised_date, zone, rider_id,
           cod_amount, updated_at
    INTO clean.parcels
    FROM ranked WHERE rn = 1;
""")
run_sql("""
    WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY parcel_id
                                     ORDER BY updated_at DESC) AS rn
        FROM clean.parcels_all
    )
    SELECT parcel_id, updated_at AS dropped_updated_at,
           CAST('superseded by a row with a later updated_at' AS NVARCHAR(80)) AS reason
    INTO clean.merge_log
    FROM ranked WHERE rn > 1;
""")

# A PRIMARY KEY is not decoration. It makes SQL Server refuse to hold a
# duplicate parcel_id ever again - the rule is enforced by the database,
# not by us remembering to check.
run_sql("ALTER TABLE clean.parcels ALTER COLUMN parcel_id NVARCHAR(20) NOT NULL;")
run_sql("ALTER TABLE clean.parcels ADD CONSTRAINT pk_clean_parcels PRIMARY KEY (parcel_id);")

print(f"\n  {table_count('clean.parcels_all'):,} rows in -> "
      f"{table_count('clean.parcels'):,} parcels kept, "
      f"{table_count('clean.merge_log')} logged as superseded")

# ===========================================================================
step(3, "SCANS - park the ones we cannot use")
# ===========================================================================
scans = fetch_df("SELECT scan_id, parcel_id, status, scanned_at, rider_id FROM raw.scans")
scans["scanned_at"] = pd.to_datetime(scans.scanned_at, errors="coerce")
scans["status"] = scans.status.str.strip().str.lower()

insert_dataframe(scans, "clean.scans_all", {
    "scan_id": "NVARCHAR(20)", "parcel_id": "NVARCHAR(20)",
    "status": "NVARCHAR(30)", "scanned_at": "DATETIME2", "rider_id": "NVARCHAR(10)",
})

# A scan for a parcel we have never heard of cannot be counted, but it also
# must not vanish. If it vanishes, raw rows stop adding up and your
# reconciliation check in step 6 can never pass.
run_sql("IF OBJECT_ID('clean.rejected_scans','U') IS NOT NULL DROP TABLE clean.rejected_scans;")
run_sql("""
    SELECT s.*, CAST('parcel_id not found in clean.parcels' AS NVARCHAR(80)) AS reason
    INTO clean.rejected_scans
    FROM clean.scans_all s
    WHERE NOT EXISTS (SELECT 1 FROM clean.parcels p WHERE p.parcel_id = s.parcel_id);
""")
print(f"\n  {table_count('clean.rejected_scans')} scans rejected (unknown parcel_id)")

# ===========================================================================
step(4, "SCANS - the 2-minute rule")
# ===========================================================================
# The handheld sometimes fires twice. Two 'delivered' scans for one parcel
# ninety seconds apart are one delivery, not two.
#
# LAG() looks at the PREVIOUS row inside the same group. Group by
# (parcel_id, status), order by time, and each row can see the scan just
# before it. If that was under 120 seconds ago, this row is an echo.
#
# prev_scan IS NULL means "there was no row before me" - the first scan of
# its kind, which we always keep.
run_sql("IF OBJECT_ID('clean.scans','U') IS NOT NULL DROP TABLE clean.scans;")
run_sql("""
    WITH gapped AS (
        SELECT s.*,
               LAG(s.scanned_at) OVER (PARTITION BY s.parcel_id, s.status
                                       ORDER BY s.scanned_at) AS prev_scan
        FROM clean.scans_all s
        WHERE EXISTS (SELECT 1 FROM clean.parcels p WHERE p.parcel_id = s.parcel_id)
    )
    SELECT scan_id, parcel_id, status, scanned_at, rider_id
    INTO clean.scans
    FROM gapped
    WHERE prev_scan IS NULL
       OR DATEDIFF(SECOND, prev_scan, scanned_at) > 120;
""")

kept, total = table_count("clean.scans"), table_count("clean.scans_all")
rejected = table_count("clean.rejected_scans")
print(f"\n  {total:,} scans -> {kept:,} kept, {rejected} rejected, "
      f"{total - kept - rejected} duplicates removed by the 2-minute rule")

# ===========================================================================
step(5, "REMITTANCES - turn the text into money")
# ===========================================================================
remits = fetch_df("SELECT remittance_id, parcel_id, rider_id, amount, remitted_at FROM raw.remittances")
print("\n  before:", list(remits.amount.head(3)))
remits["amount"] = to_money(remits.amount)
print("  after: ", list(remits.amount.head(3)))

remits["remitted_at"] = pd.to_datetime(remits.remitted_at, errors="coerce")
remits["rider_id"] = remits.rider_id.str.strip().str.upper()

bad = remits.amount.isna().sum()
if bad:
    print(f"  WARNING: {bad} amounts could not be parsed - look at them before trusting totals")

insert_dataframe(remits, "clean.remittances", {
    "remittance_id": "NVARCHAR(20)", "parcel_id": "NVARCHAR(20)",
    "rider_id": "NVARCHAR(10)", "amount": "DECIMAL(10,2)", "remitted_at": "DATETIME2",
})
total_cash = fetch_df("SELECT SUM(amount) AS t FROM clean.remittances").t[0]
print(f"\n  clean.remittances: {table_count('clean.remittances'):,} rows, "
      f"total Rs {total_cash:,.0f}")

done("Four clean tables, and two tables of evidence for what we removed.\n"
     "     Next:  python 04_build_parcel_final.py")
