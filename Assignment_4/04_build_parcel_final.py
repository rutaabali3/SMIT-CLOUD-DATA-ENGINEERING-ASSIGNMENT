"""
=============================================================================
 STEP 4 - ONE ROW PER PARCEL, WITH THE TRUTH ON IT          (about 8 minutes)
=============================================================================

    python 04_build_parcel_final.py

Everything so far has been housekeeping. This is the first step that makes
a DECISION about the business.

A parcel has many scans. Finance does not care about scans - Finance cares
about one line per parcel:

    did it arrive, when, and does the rider owe us cash for it?

That is what clean.parcel_final holds, and every question in step 5 reads
from it rather than re-deriving it. Build the hard thing once.

The two rules that do the work:

  RULE 3   A parcel's final status is the status of its LATEST scan.
           Not "is there a delivered scan anywhere" - the latest one wins.
           A parcel scanned delivered and then returned was returned.

  RULE 4   cod_due = cod_amount, but ONLY if the final status is delivered.
           A parcel still in transit owes nothing. A returned parcel owes
           nothing. This single CASE expression is where most of the
           missing cash is about to come from.
=============================================================================
"""
from db import banner, done, fetch_df, run_sql, step, table_count

banner("STEP 4 - BUILDING clean.parcel_final")

# ===========================================================================
step(1, "Find each parcel's LAST scan")
# ===========================================================================
# Same window function as step 3, pointed at a different question.
# ROW_NUMBER() ordered by scanned_at DESC puts the newest scan at rn = 1.
#
# Why not MAX(scanned_at)? Because we need the STATUS that came with that
# newest row, not just its timestamp. MAX gives you one column; ROW_NUMBER
# gives you the whole winning row. That is the difference worth remembering.
run_sql("IF OBJECT_ID('clean.parcel_final','U') IS NOT NULL DROP TABLE clean.parcel_final;")
run_sql("""
    WITH last_scan AS (
        SELECT parcel_id, status, scanned_at,
               ROW_NUMBER() OVER (PARTITION BY parcel_id
                                  ORDER BY scanned_at DESC) AS rn
        FROM clean.scans
    )
    SELECT
        p.parcel_id,
        p.zone,
        p.rider_id,
        p.booked_date,
        p.promised_date,
        p.cod_amount,

        -- A parcel with no usable scan at all is not "delivered" and it is
        -- not an error either - it is simply 'no_scan'. Name it, do not
        -- leave it NULL for someone else to trip over.
        ISNULL(ls.status, 'no_scan')                       AS final_status,

        -- Only a delivery has a delivery date.
        CASE WHEN ls.status = 'delivered'
             THEN CAST(ls.scanned_at AS DATE) END          AS delivered_date,

        -- RULE 4. The whole case study turns on this expression.
        CASE WHEN ls.status = 'delivered'
             THEN p.cod_amount ELSE 0 END                  AS cod_due,

        -- RULE 5. On time = delivered on or before the promise.
        CASE WHEN ls.status = 'delivered'
                  AND CAST(ls.scanned_at AS DATE) <= p.promised_date
             THEN 1 ELSE 0 END                             AS on_time
    INTO clean.parcel_final
    FROM clean.parcels p
    LEFT JOIN last_scan ls
           ON ls.parcel_id = p.parcel_id AND ls.rn = 1;
""")

# LEFT JOIN, not JOIN. An inner join would silently drop every parcel that
# has no scan - and those are exactly the parcels somebody should be asking
# about. Never let a join decide what counts as real.
run_sql("ALTER TABLE clean.parcel_final ALTER COLUMN parcel_id NVARCHAR(20) NOT NULL;")
run_sql("ALTER TABLE clean.parcel_final ADD CONSTRAINT pk_parcel_final PRIMARY KEY (parcel_id);")

print(f"\n  clean.parcel_final: {table_count('clean.parcel_final'):,} rows "
      f"(one per parcel in clean.parcels - {table_count('clean.parcels'):,})")

# ===========================================================================
step(2, "What did we just build?")
# ===========================================================================
print()
print(fetch_df("""
    SELECT final_status,
           COUNT(*)                     AS parcels,
           SUM(cod_due)                 AS cod_due,
           SUM(cod_amount)              AS cod_on_the_parcels
    FROM clean.parcel_final
    GROUP BY final_status
    ORDER BY parcels DESC;
""").to_string(index=False))

print("\n  Read the two money columns side by side. 'cod_on_the_parcels' is")
print("  what the parcels were worth; 'cod_due' is what a rider actually owes")
print("  us. Everything that is not 'delivered' owes nothing - that gap is")
print("  rule 4 doing its job.")

# ===========================================================================
step(3, "The sanity check that catches a broken join")
# ===========================================================================
# If this ever prints a number other than 0, something upstream is wrong and
# every answer in step 5 is wrong with it. Check the cheap thing early.
bad = fetch_df("""
    SELECT COUNT(*) AS n FROM clean.parcel_final
    WHERE delivered_date < booked_date
""").n[0]
print(f"\n  parcels 'delivered' before they were booked: {bad}  (must be 0)")
if bad:
    raise SystemExit("  Time is running backwards. Fix step 3 before continuing.")

done("One trustworthy row per parcel. Every question now reads from here.\n"
     "     Next:  python 05_answer_the_questions.py")
