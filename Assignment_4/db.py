"""
=============================================================================
 DB - every conversation with SQL Server goes through this file
=============================================================================

Why does this file exist?
    Opening a database connection is five lines of boilerplate. Doing it in
    eight different scripts means the same five lines, eight times, and eight
    places to fix when something changes.

    So we write small helpers once, here, and the rest of the project reads
    like what it actually does:

        df = fetch_df("SELECT * FROM raw.parcels")

    instead of connection-handling noise.

You do not need to edit this file. Read it once so you know what the
helpers do, then use them.
=============================================================================
"""
import re
import warnings
from pathlib import Path

import pandas as pd
import pyodbc

from config import CONNECTION_STRING

# pandas prefers a library called SQLAlchemy and prints a warning every time
# we hand it a plain pyodbc connection. We use pyodbc on purpose (one less
# thing to install, and you can see the real SQL), so we silence the noise.
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")


def get_connection(autocommit=False):
    """
    Open a connection to SQL Server.

    autocommit=True means "run each statement immediately".
    autocommit=False (the default) means "hold the changes until I call
    conn.commit()" - which is what you want when inserting many rows,
    because committing once is far faster than committing 6,000 times.
    """
    return pyodbc.connect(CONNECTION_STRING, autocommit=autocommit)


def run_sql(sql, params=()):
    """Run a statement that returns no rows: CREATE, DELETE, UPDATE, DROP."""
    with get_connection(autocommit=True) as conn:
        conn.cursor().execute(sql, params)


def fetch_df(sql, params=()):
    """Run a SELECT and hand the result back as a pandas DataFrame."""
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def fetch_value(sql, params=()):
    """Run a SELECT that returns ONE number, and give back just that number."""
    with get_connection() as conn:
        return conn.cursor().execute(sql, params).fetchone()[0]


def table_count(table):
    """How many rows are in this table? e.g. table_count('raw.parcels')"""
    return fetch_value(f"SELECT COUNT(*) FROM {table}")


def table_exists(table):
    """Does this table exist yet? Used to give friendly 'run step N first'
    messages instead of a confusing SQL error."""
    return fetch_value("SELECT COUNT(*) FROM sys.objects WHERE object_id = OBJECT_ID(?)",
                       (table,)) > 0


def run_sql_script(path):
    """
    Run a .sql FILE that contains several statements separated by GO.

    `GO` is not actually SQL - it is a word the sqlcmd tool understands,
    meaning "send everything above this line to the server now". pyodbc does
    not know it, so we split the file on GO ourselves and send one chunk at
    a time.
    """
    sql = Path(path).read_text(encoding="utf-8")
    chunks = [c.strip() for c in re.split(r"(?mi)^\s*GO\s*$", sql) if c.strip()]
    with get_connection(autocommit=True) as conn:
        cursor = conn.cursor()
        for chunk in chunks:
            cursor.execute(chunk)


def insert_dataframe(df, table, column_types, chunk_size=5000):
    """
    Drop a table, recreate it with proper column types, and fill it from a
    DataFrame.

    Two things here are worth understanding:

    1. DROP-then-CREATE makes the step IDEMPOTENT: run it once or ten times,
       you end up with exactly the same table. That matters in class, because
       somebody always runs a script twice.

    2. cursor.fast_executemany = True is the single most important line.
       Without it, pyodbc sends rows to the server ONE AT A TIME - 6,000
       separate round trips, which takes minutes. With it, rows go in batches
       and the same load takes seconds.
    """
    columns = list(column_types.keys())
    column_defs = ", ".join(f"[{c}] {column_types[c]}" for c in columns)

    # pandas marks "missing" as NaN or NaT. SQL Server wants None (= NULL).
    data = df[columns].astype(object).where(pd.notna(df[columns]), None)
    rows = data.values.tolist()

    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(f"[{c}]" for c in columns)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"IF OBJECT_ID('{table}','U') IS NOT NULL DROP TABLE {table};")
        cursor.execute(f"CREATE TABLE {table} ({column_defs});")

        cursor.fast_executemany = True
        sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
        for start in range(0, len(rows), chunk_size):
            cursor.executemany(sql, rows[start:start + chunk_size])

        conn.commit()      # nothing is saved until this line runs

    return len(rows)


# ---------------------------------------------------------------------------
# Small helpers so every script prints in the same style
# ---------------------------------------------------------------------------
def banner(title):
    print()
    print("=" * 72)
    print(f" {title}")
    print("=" * 72)


def step(number, title):
    print(f"\n  STEP {number}: {title}")


def done(message):
    print(f"\n  >> {message}")
