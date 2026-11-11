"""
=============================================================================
 RUN EVERYTHING - the catch-up button
=============================================================================

    python run_all.py              run steps 1 to 6 in order
    python run_all.py --from 3     start at step 3 (skips profiling and load)
    python run_all.py --quiet      only show each step's last few lines

IF YOU FALL BEHIND IN CLASS, USE THIS. Every step is idempotent - running
it again gives exactly the same result - so you can rejoin at any point
without breaking anything.

A full run takes well under a minute. It does NOT run 00_test_connection.py:
run that yourself, once, before anything else.
=============================================================================
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

STEPS = [
    ("01_profile_the_data.py",     "Look at the files"),
    ("02_load_raw.py",             "Load them into SQL Server"),
    ("03_clean_tables.py",         "Clean the three tables"),
    ("04_build_parcel_final.py",   "One row per parcel"),
    ("05_answer_the_questions.py", "Answer Finance's five questions"),
    ("06_quality_checks.py",       "Prove the numbers"),
]


def main():
    start_at = 1
    if "--from" in sys.argv:
        start_at = int(sys.argv[sys.argv.index("--from") + 1])
    quiet = "--quiet" in sys.argv

    # If the data was never generated, every step below fails confusingly.
    # One check here beats six mysterious errors.
    if not (HERE / "data" / "parcels.csv").exists():
        sys.exit("No data found. Run this first:\n\n    python make_data.py\n")

    began = time.time()

    for number, (script, title) in enumerate(STEPS, start=1):
        if number < start_at:
            print(f"  ..  skipping step {number}: {title}")
            continue

        print()
        print("#" * 72)
        print(f"#  STEP {number} - {title}   ({script})")
        print("#" * 72, flush=True)

        result = subprocess.run([sys.executable, str(HERE / script)],
                                cwd=HERE, capture_output=quiet, text=True)

        if quiet and result.stdout:
            for line in result.stdout.strip().splitlines()[-6:]:
                print(line)

        if result.returncode != 0:
            if quiet and result.stdout:
                print(result.stdout[-2000:])
            if quiet and result.stderr:
                print(result.stderr[-2000:])
            sys.exit(f"\nSTOPPED: {script} failed. Fix that before continuing.")

    print()
    print("#" * 72)
    print(f"#  ALL STEPS FINISHED in {time.time() - began:.0f} seconds.")
    print("#  Your answers are in results/. Now write findings.md.")
    print("#" * 72)


if __name__ == "__main__":
    main()
