"""
=============================================================================
 CONFIG - all the settings for the whole project, in ONE file
=============================================================================

Why does this file exist?
    Every script here needs two things: where the CSV files are, and how to
    reach SQL Server. If each script had its own copy of that, moving to a
    different computer would mean editing seven files. So we write it once,
    here, and every other script imports it.

This is the ONLY file you should need to edit to run the project - and most
of the time you edit `.env` instead, not even this.
=============================================================================
"""
import os
from pathlib import Path

# This folder (mini-sprint-riderdrop), wherever it lives on your computer.
PROJECT_DIR = Path(__file__).resolve().parent


# -----------------------------------------------------------------------
# 0. READ THE .env FILE
# -----------------------------------------------------------------------
# Server names, logins and passwords do not belong in code. They differ on
# every machine, and a password committed to git is a password you have
# given away. So they live in `.env`, which is in `.gitignore` and therefore
# never reaches GitHub.
#
# `.env.example` IS committed. It lists the setting names with no values, so
# the next person knows what to fill in. Copy it to `.env` and edit that.
#
# A .env file is just NAME=value lines. Reading it is eight lines of Python,
# so we do not install a library for it.
# -----------------------------------------------------------------------
def _load_dotenv():
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return False

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        # setdefault, not assignment: a real environment variable set in the
        # terminal WINS over this file. That lets you override one setting
        # for one run - $env:SQL_DATABASE = "test" - without editing a file.
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))

    return True


DOTENV_LOADED = _load_dotenv()


# -----------------------------------------------------------------------
# 1. WHERE ARE THE DATA FILES?
# -----------------------------------------------------------------------
# Unlike a normal project, our CSVs are GENERATED, not downloaded:
#     python make_data.py
# writes them into ./data. We still look in a couple of places, so the
# project survives being moved around.
# -----------------------------------------------------------------------
DATA_FILES = ["parcels.csv", "scans.csv", "cod_remittances.csv"]


def _find_data_dir():
    candidates = []
    if os.environ.get("DATA_DIR"):
        candidates.append(Path(os.environ["DATA_DIR"]))
    candidates += [PROJECT_DIR / "data", PROJECT_DIR.parent / "data"]

    for folder in candidates:
        # parcels.csv is our "is this really the data folder?" marker.
        if (folder / "parcels.csv").exists():
            return folder

    # Nothing found. Return the first choice so the error message later can
    # show the user where we looked.
    return PROJECT_DIR / "data"


DATA_DIR = _find_data_dir()

# Where 05_answer_the_questions.py drops its CSVs.
RESULTS_DIR = PROJECT_DIR / "results"


# -----------------------------------------------------------------------
# 2. HOW DO WE REACH SQL SERVER?
# -----------------------------------------------------------------------
# A connection string is a sentence telling the driver where the database
# is and how to log in. Ours has five parts:
#
#   DRIVER   which ODBC driver to use ("ODBC Driver 18 for SQL Server")
#   SERVER   where the database is. "localhost" = this computer.
#   DATABASE which database on that server
#   auth     either your Windows login, or a username + password
#   TrustServerCertificate=yes
#            accept the local development certificate. Fine on localhost.
#            You would NOT do this against a real production server.
#
# Every value comes from .env (or the terminal) if you set it there, and
# falls back to the default written here if you did not.
# -----------------------------------------------------------------------
SQL_SERVER   = os.environ.get("SQL_SERVER", "localhost")
# IMPORTANT IF YOUR CLASS SHARES ONE SQL SERVER: everybody would write into
# the same database and overwrite each other. Give yourself your own name
# in .env before running anything:   SQL_DATABASE=riderdrop_yourname
SQL_DATABASE = os.environ.get("SQL_DATABASE", "riderdrop_class")
SQL_DRIVER   = os.environ.get("SQL_DRIVER", "ODBC Driver 18 for SQL Server")

# Blank on purpose. A password typed into a .py file gets committed; a
# password in .env does not. Fill these in .env only if Windows auth fails.
SQL_USER     = os.environ.get("SQL_USER", "")
SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "")


def connection_string(database=None):
    """
    Build the connection sentence.

    We pass `database` separately because 00_test_connection.py needs to
    connect to `master` (the system database that always exists) BEFORE our
    own database has been created.
    """
    database = database or SQL_DATABASE

    if SQL_USER:
        # Username and password (Docker, or a shared class server)
        login = f"UID={SQL_USER};PWD={SQL_PASSWORD};"
    else:
        # WINDOWS AUTHENTICATION - your Windows login. Nothing to type,
        # nothing to leak. This is the default and the one you want.
        login = "Trusted_Connection=yes;"

    return (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={database};"
        f"{login}"
        "TrustServerCertificate=yes;"
    )


CONNECTION_STRING = connection_string()
