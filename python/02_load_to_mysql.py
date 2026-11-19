"""
Ola Ride Insights - Step 3b: Load ola_cleaned.csv into MySQL
-------------------------------------------------------------
Run AFTER 01_create_table.sql has been executed in MySQL Workbench.

Install once:
    pip install pandas sqlalchemy pymysql cryptography

Usage:
    python 02_load_to_mysql.py
"""

import getpass
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------- settings: change if yours differ ----------------
HOST = "localhost"
PORT = 3306
USER = "root"
DATABASE = "ola_db"
TABLE = "ola_rides"
CSV_FILE = "data/ola_cleaned.csv"
# ------------------------------------------------------------------

password = getpass.getpass(f"MySQL password for '{USER}': ")
engine = create_engine(
    f"mysql+pymysql://{USER}:{quote_plus(password)}@{HOST}:{PORT}/{DATABASE}"
)

# 1. Read the CSV and get the types right ---------------------------------
df = pd.read_csv(CSV_FILE)
print(f"Read {len(df):,} rows x {df.shape[1]} columns from {CSV_FILE}")

df["booking_datetime"] = pd.to_datetime(df["booking_datetime"])
df["booking_date"] = pd.to_datetime(df["booking_date"]).dt.date
# booking_time stays as 'HH:MM:SS' text, which MySQL accepts for TIME

# whole-number columns that contain NULLs -> nullable integer
for col in ["v_tat", "c_tat"]:
    df[col] = df[col].astype("Int64")

# make every missing value a real Python None so MySQL stores NULL
df = df.astype(object).where(df.notna(), None)

# 2. Load -----------------------------------------------------------------
with engine.begin() as conn:
    conn.execute(text(f"TRUNCATE TABLE {TABLE}"))   # safe to re-run

df.to_sql(TABLE, engine, if_exists="append", index=False, chunksize=5000)

# 3. Verify ---------------------------------------------------------------
with engine.connect() as conn:
    total = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar()
    success = conn.execute(
        text(f"SELECT COUNT(*) FROM {TABLE} WHERE booking_status = 'Success'")
    ).scalar()

print(f"\nRows in MySQL table '{TABLE}': {total:,}   (expected 103,024)")
print(f"Successful bookings:            {success:,}   (expected 63,967)")
print("Load OK." if (total, success) == (103_024, 63_967) else "Check the numbers above!")