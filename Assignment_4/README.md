# RiderDrop — a 45-minute data engineering sprint

You are handed **three messy courier export files** and one question from Finance:

> September's cash book is short. Operations says every parcel was delivered.
> How much cash is missing, and who is holding it?

Nobody can answer it, because no system joins parcels, scans and cash together.
By the end of this sprint you will have built the pipeline that does — and a number
you could defend in front of a finance director.

**Stack:** Python (pandas + pyodbc) and Microsoft SQL Server, with Windows authentication.

---

## Which file do I run?

In order. Each one prints what to run next, so you can follow the trail.

```powershell
python make_data.py            # once - generates the three CSVs into data/
python 00_test_connection.py   # once - checks Python, pyodbc, the driver, SQL Server
python run_all.py              # runs steps 1 to 6 (under a minute)
```

`run_all.py` is the catch-up button. To work through it properly, run the steps
one at a time instead — that is the point of the exercise:

| Script | What it does | Time |
|---|---|---|
| `make_data.py` | Writes `data/parcels.csv`, `scans.csv`, `cod_remittances.csv` | — |
| `00_test_connection.py` | Six setup checks, each with a FIX line if it fails | 2 min |
| `01_profile_the_data.py` | Look at the files. Finds the five planted problems. Writes nothing. | 5 min |
| `02_load_raw.py` | Loads all three files into `raw.*` as text, then reconciles row counts | 5 min |
| `03_clean_tables.py` | Types, dedupe, the 2-minute rule, money parsing → `clean.*` | 15 min |
| `04_build_parcel_final.py` | One row per parcel: final status, `cod_due`, on-time | 8 min |
| `05_answer_the_questions.py` | The five questions → `results/*.csv` | 12 min |
| `06_quality_checks.py` | 11 checks → `dq.results` | 5 min |

The brief students work from is **`CASE_STUDY.pdf`** (built from `CASE_STUDY.md` by
`python md2pdf.py`).

## Setup

### 1. Install the two libraries

```powershell
pip install -r requirements.txt
```

### 2. Make your settings file

```powershell
Copy-Item .env.example .env
```

**`.env` is where the server name, the database name and any login come from.**
`config.py` reads it on startup; every script imports `config.py`; nothing else
touches it. Open it — every setting is listed and commented out, with the default
written next to it.

> **If your whole class shares one SQL Server**, give yourself your own database
> or you will all overwrite each other. In `.env`:
> ```
> SQL_DATABASE=riderdrop_yourname
> ```
>
> **Named instance?** In `.env`:
> ```
> SQL_SERVER=localhost\SQLEXPRESS
> ```
>
> **If your SQL Server does not accept your Windows login** (Docker, Linux, a shared
> class server), add a username and password. In `.env`:
> ```
> SQL_USER=sa
> SQL_PASSWORD=your-password
> ```
> Leave both out if you can. No user means `Trusted_Connection=yes` — **Windows
> authentication**, your own login, with nothing to type and nothing to leak.

**Why two files?** `.env.example` is committed to git and holds the setting *names*.
`.env` is in `.gitignore` and holds *your* values. That is how a password stays off
GitHub, and you will see this pattern in every real repo you work in. A real
environment variable still beats the file, so `$env:SQL_DATABASE = "scratch"`
overrides it for one run without editing anything.

### 3. Check it

```powershell
python 00_test_connection.py
```

Every line should say `OK`. If one says `FAIL`, read the `FIX` line under it — it
tells you the exact command. Do not skip ahead; nothing else runs until these pass.

## What gets built

```
raw.parcels, raw.scans, raw.remittances     untouched copies, every column text
clean.parcels          1,200 parcels, deduplicated, typed
clean.merge_log        the 40 superseded rows and why they lost
clean.scans            duplicate scans removed by the 2-minute rule
clean.rejected_scans   the 30 scans whose parcel does not exist, with a reason
clean.remittances      amount as DECIMAL you can actually SUM
clean.parcel_final     one row per parcel: final status, cod_due, on_time
dq.results             11 checks, passed/failed, with detail
```

Two schemas, on purpose: from the table name alone you can always tell whether you
are looking at **evidence** (`raw`) or at a **conclusion** (`clean`).

## The five planted problems

`01_profile_the_data.py` shows you all five before you fix any of them:

1. 40 duplicate `parcel_id` rows — keep the latest `updated_at`
2. Three date formats in one column — including the ambiguous `11/09/2026`
3. Zone names in mixed case with stray spaces — 30+ values that should be 4
4. `amount` stored as text — `Rs 1,250`, `1250.00`, `" 1250 "`
5. 30 scans pointing at parcels that do not exist

Plus one that only shows up after you join: 345 duplicate scans seconds apart.

> **The date one is the trap.** `pd.to_datetime(col, format="mixed", dayfirst=True)`
> looks like the tidy answer and is wrong on this data — it reads `11/09/2026` as
> 9 November, not 11 September. Nothing warns you. You get parcels delivered two
> months before they were booked, and you only find out because a sanity check in
> step 4 asks. See the comment in `to_date()` in `03_clean_tables.py`.

## Deliverable

Three bullets in `findings.md`, each with a rupee number, the query that produced
it, and what Finance should do on Monday. The pipeline is just how you earn the
right to write them.

## Instructor notes

- `python make_data.py --check` regenerates the data and asserts every planted
  issue is present. Seeded, so everyone gets identical numbers.
- The headline is **Rs 657,130** short, 10.5% of what was due. Four riders carry
  most of it, and Rs 759,440 sits on 100 delivered parcels with no remittance row
  at all — larger than the net gap, because cash also arrived against parcels that
  were never delivered. Netting the two is how it stayed invisible.
- To stretch this to 90 minutes, delete `03`–`06` and hand students only
  `CASE_STUDY.pdf`, `00`, `01` and `db.py`.
