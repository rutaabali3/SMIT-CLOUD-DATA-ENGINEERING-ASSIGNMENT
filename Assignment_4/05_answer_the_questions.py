"""
=============================================================================
 STEP 5 - ANSWER FINANCE'S FIVE QUESTIONS                  (about 12 minutes)
=============================================================================

    python 05_answer_the_questions.py

This step reads the clean data model (primarily clean.parcel_final and
clean.remittances), runs the five analytical queries, prints the business
findings, and exports all results to CSV in the results/ folder.
=============================================================================
"""
from pathlib import Path
import pandas as pd

from config import RESULTS_DIR
from db import banner, done, fetch_df, step

banner("STEP 5 - ANSWERING FINANCE'S FIVE QUESTIONS")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
QUERIES_DIR = Path(__file__).parent / "queries"

# ===========================================================================
step(0, "Export clean.parcel_final master table to CSV")
# ===========================================================================
df_final = fetch_df("""
    SELECT 
        parcel_id,
        zone,
        rider_id,
        booked_date,
        promised_date,
        cod_amount,
        final_status,
        delivered_date,
        cod_due,
        on_time
    FROM clean.parcel_final
    ORDER BY parcel_id;
""")
parcel_final_csv = RESULTS_DIR / "parcel_final.csv"
df_final.to_csv(parcel_final_csv, index=False)
print(f"\n  Exported {len(df_final):,} rows to {parcel_final_csv}")

# ===========================================================================
step(1, "Question 1: Parcel count by zone and final status")
# ===========================================================================
q1_sql = (QUERIES_DIR / "q1.sql").read_text(encoding="utf-8")
df_q1 = fetch_df(q1_sql)
df_q1.to_csv(RESULTS_DIR / "q1.csv", index=False)
df_q1.to_csv(RESULTS_DIR / "q1_parcel_count_by_zone_status.csv", index=False)
print("\n" + df_q1.to_string(index=False))

# ===========================================================================
step(2, "Question 2: On-time delivery rate by zone")
# ===========================================================================
q2_sql = (QUERIES_DIR / "q2.sql").read_text(encoding="utf-8")
df_q2 = fetch_df(q2_sql)
df_q2.to_csv(RESULTS_DIR / "q2.csv", index=False)
df_q2.to_csv(RESULTS_DIR / "q2_ontime_rate_by_zone.csv", index=False)
print("\n" + df_q2.to_string(index=False))

# ===========================================================================
step(3, "Question 3: Top 5 riders by total COD shortfall")
# ===========================================================================
q3_sql = (QUERIES_DIR / "q3.sql").read_text(encoding="utf-8")
df_q3 = fetch_df(q3_sql)
df_q3.to_csv(RESULTS_DIR / "q3.csv", index=False)
df_q3.to_csv(RESULTS_DIR / "q3_top5_riders_shortfall.csv", index=False)
print("\n" + df_q3.to_string(index=False))

# ===========================================================================
step(4, "Question 4: Parcels with a remittance but final status NOT delivered")
# ===========================================================================
q4_sql = (QUERIES_DIR / "q4.sql").read_text(encoding="utf-8")
df_q4 = fetch_df(q4_sql)
df_q4.to_csv(RESULTS_DIR / "q4.csv", index=False)
df_q4.to_csv(RESULTS_DIR / "q4_remittance_not_delivered.csv", index=False)
print(f"\n  Found {len(df_q4)} parcels with remittances but not marked delivered:")
print(f"  Total amount remitted for these parcels: Rs {df_q4['remitted_amount'].sum():,.2f}")
print(df_q4.head(10).to_string(index=False))

# ===========================================================================
step(5, "Question 5: Delivered COD parcels with NO remittance")
# ===========================================================================
q5_sql = (QUERIES_DIR / "q5.sql").read_text(encoding="utf-8")
df_q5_summary = fetch_df(q5_sql)
df_q5_summary.to_csv(RESULTS_DIR / "q5.csv", index=False)
df_q5_summary.to_csv(RESULTS_DIR / "q5_delivered_no_remittance_summary.csv", index=False)
print("\n" + df_q5_summary.to_string(index=False))

# Also export full detail of unremitted delivered COD parcels for Finance to audit
df_q5_detail = fetch_df("""
    SELECT
        p.parcel_id,
        p.rider_id,
        p.zone,
        p.booked_date,
        p.delivered_date,
        p.cod_due AS rupees_at_risk
    FROM clean.parcel_final p
    LEFT JOIN clean.remittances r ON p.parcel_id = r.parcel_id
    WHERE p.final_status = 'delivered'
      AND p.cod_due > 0
      AND r.parcel_id IS NULL
    ORDER BY p.cod_due DESC, p.parcel_id;
""")
df_q5_detail.to_csv(RESULTS_DIR / "q5_delivered_no_remittance_details.csv", index=False)
print(f"\n  Exported {len(df_q5_detail)} detailed records to q5_delivered_no_remittance_details.csv")

done("All 5 questions answered and exported to results/*.csv\n"
     "     Next:  python 06_quality_checks.py")
