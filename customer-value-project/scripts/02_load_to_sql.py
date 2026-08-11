"""
Phase 2a - Load the cleaned dataset into a real SQL database (SQLite).
SQLite ships with Python, so there's nothing extra to install.
"""

import sqlite3
import pandas as pd

CSV_PATH = "data/customers_clean.csv"
DB_PATH = "customer_intelligence.db"

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df):,} rows from {CSV_PATH}")

conn = sqlite3.connect(DB_PATH)
df.to_sql("customers", conn, if_exists="replace", index=False)

check = pd.read_sql("SELECT COUNT(*) AS n FROM customers;", conn)
print(f"Loaded into SQLite table 'customers' -> {check['n'][0]:,} rows")

schema = pd.read_sql("PRAGMA table_info(customers);", conn)
print(f"\nTable schema ({len(schema)} columns):")
print(schema[["name", "type"]].to_string(index=False))

conn.close()
print(f"\nSQLite database ready -> {DB_PATH}")