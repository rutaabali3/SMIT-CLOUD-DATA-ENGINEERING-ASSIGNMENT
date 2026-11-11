"""
=============================================================================
 STEP 0 - DOES EVERYTHING WORK?            (run this FIRST - about 2 minutes)
=============================================================================

    python 00_test_connection.py

This script does not touch the project. Its only job is to check the six
things that have to be true before anything else can run, and to tell you
EXACTLY what to do if one of them is not.

    1. Python version
    2. pandas is installed
    3. pyodbc is installed
    4. the SQL Server ODBC driver is installed
    5. SQL Server is reachable and will let you log in (Windows auth)
    6. the three data files exist

If every line says OK, you are ready. If one says FAIL, read the "FIX"
underneath it - it tells you the command to run.
=============================================================================
"""
import sys

PASS, FAIL = "  OK  ", " FAIL "
results = []


def check(ok, label, detail="", fix=""):
    """Record and print one check."""
    results.append(ok)
    print(f"[{PASS if ok else FAIL}] {label}")
    if detail:
        print(f"         {detail}")
    if not ok and fix:
        for line in fix.strip().splitlines():
            print(f"         FIX: {line.strip()}")
    return ok


print()
print("=" * 72)
print(" CHECKING YOUR SETUP")
print("=" * 72)
print()

# ---------------------------------------------------------------------------
# 1. Python
# ---------------------------------------------------------------------------
version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
check(sys.version_info >= (3, 9), "Python 3.9 or newer", f"you have Python {version}",
      "Install Python 3.9+ from python.org")

# ---------------------------------------------------------------------------
# 2 and 3. The two libraries we need
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    check(True, "pandas is installed", f"version {pd.__version__}")
except ImportError:
    check(False, "pandas is installed", "not found", "pip install -r requirements.txt")

try:
    import pyodbc
    check(True, "pyodbc is installed", f"version {pyodbc.version}")
except ImportError:
    pyodbc = None
    check(False, "pyodbc is installed", "not found", "pip install -r requirements.txt")

# ---------------------------------------------------------------------------
# 4. The ODBC driver
#    pyodbc is the Python side. The DRIVER is a separate piece of Microsoft
#    software that actually speaks to SQL Server. People forget this one.
# ---------------------------------------------------------------------------
driver_ok = False
if pyodbc:
    drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
    preferred = [d for d in drivers if "18" in d or "17" in d]
    driver_ok = check(
        bool(preferred),
        "SQL Server ODBC driver is installed",
        f"found: {', '.join(drivers) if drivers else 'none'}",
        """Download "ODBC Driver 18 for SQL Server" from Microsoft and install it.
           Search: microsoft odbc driver 18 for sql server download""")

# ---------------------------------------------------------------------------
# 5. Can we reach SQL Server and log in?
#    We connect to `master`, the system database that always exists, because
#    our own database has not been created yet.
# ---------------------------------------------------------------------------
server_ok = False
if pyodbc and driver_ok:
    from config import (DOTENV_LOADED, SQL_DATABASE, SQL_SERVER, SQL_USER,
                        connection_string)

    # Where did these settings come from? Worth knowing before you spend ten
    # minutes wondering why editing .env changed nothing.
    print(f"    settings: .env {'read' if DOTENV_LOADED else 'NOT FOUND - using defaults'}"
          f"  |  server={SQL_SERVER}  database={SQL_DATABASE}"
          f"  |  login={'user ' + SQL_USER if SQL_USER else 'Windows authentication'}")

    how = f"user '{SQL_USER}'" if SQL_USER else "your Windows login"
    try:
        with pyodbc.connect(connection_string("master"), timeout=5) as conn:
            row = conn.cursor().execute(
                "SELECT CAST(SERVERPROPERTY('Edition') AS NVARCHAR(100)), SUSER_SNAME()"
            ).fetchone()
        server_ok = check(True, f"SQL Server at '{SQL_SERVER}' answers",
                          f"{row[0]}, connected with {how} as {row[1]}")
    except Exception as error:
        first_line = str(error).split("\n")[0][:150]
        check(False, f"SQL Server at '{SQL_SERVER}' answers", first_line,
              r"""Is SQL Server running? In PowerShell:  Get-Service MSSQL*
                 No .env file yet?   Copy-Item .env.example .env
                 Named instance? In .env:  SQL_SERVER=localhost\SQLEXPRESS
                 Windows login refused (Docker/Linux/shared server)? In .env:
                   SQL_USER=sa
                   SQL_PASSWORD=your-password""")

    # Can we create a database? Step 2 needs that.
    if server_ok:
        try:
            with pyodbc.connect(connection_string("master"), timeout=5,
                                autocommit=True) as conn:
                conn.cursor().execute(
                    f"IF DB_ID('{SQL_DATABASE}') IS NULL CREATE DATABASE [{SQL_DATABASE}];")
            check(True, f"database '{SQL_DATABASE}' is ready",
                  "created it, or it already existed")
        except Exception as error:
            check(False, f"database '{SQL_DATABASE}' is ready",
                  str(error).split("\n")[0][:150],
                  "Your login needs permission to create a database. Ask your instructor.")

# ---------------------------------------------------------------------------
# 6. The data files
#    Ours are generated, not downloaded - so the fix is one command.
# ---------------------------------------------------------------------------
from config import DATA_DIR, DATA_FILES, PROJECT_DIR   # noqa: E402

missing = [f for f in DATA_FILES if not (DATA_DIR / f).exists()]
check(not missing,
      "all 3 data files found",
      f"looking in: {DATA_DIR}" if not missing
      else f"looking in {DATA_DIR} - missing: {', '.join(missing)}",
      "python make_data.py")

# A quick size check catches a half-written or truncated file.
if not missing:
    small = [f for f in DATA_FILES if (DATA_DIR / f).stat().st_size < 10_000]
    check(not small, "the data files look complete",
          ", ".join(f"{f} {(DATA_DIR / f).stat().st_size // 1024} KB" for f in DATA_FILES),
          "python make_data.py --check")

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
print()
print("=" * 72)
if all(results):
    print(" ALL CHECKS PASSED - you are ready.")
    print()
    print(" Next:  python 01_profile_the_data.py")
else:
    print(f" {results.count(False)} CHECK(S) FAILED - fix those first.")
    print()
    print(" Read the FIX lines above. Ask for help if a fix does not work -")
    print(" do not skip ahead, because nothing else will run until these pass.")
print("=" * 72)
print()

sys.exit(0 if all(results) else 1)
