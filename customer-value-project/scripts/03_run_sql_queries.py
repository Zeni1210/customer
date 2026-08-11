"""
Phase 2b - Run every segmentation query in sql/segmentation_queries.sql
against the SQLite database, print a preview of each, and export the full
result of each to outputs/<query_name>.csv (or _1, _2... if a query block
contains more than one SELECT statement).
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "customer_intelligence.db"
SQL_PATH = "sql/segmentation_queries.sql"
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)

sql_text = Path(SQL_PATH).read_text()

# Split the file on '-- === QUERY: name ===' marker comments.
blocks = re.split(r"--\s*===\s*QUERY:\s*(\w+)\s*===", sql_text)
# blocks[0] is the file header before the first marker; after that it's
# [name, sql, name, sql, ...]
named_blocks = list(zip(blocks[1::2], blocks[2::2]))

conn = sqlite3.connect(DB_PATH)

print(f"Found {len(named_blocks)} query blocks in {SQL_PATH}\n")

for name, block_sql in named_blocks:
    # A block can contain more than one statement (see q7); run each
    # separately so every SELECT gets its own preview + CSV.
    statements = [s.strip() for s in block_sql.split(";") if s.strip()]

    for i, stmt in enumerate(statements, start=1):
        label = name if len(statements) == 1 else f"{name}_{i}"
        result = pd.read_sql(stmt, conn)

        print(f"=== {label} ({len(result)} rows) ===")
        print(result.head(10).to_string(index=False))
        print()

        out_path = OUT_DIR / f"{label}.csv"
        result.to_csv(out_path, index=False)

conn.close()
print(f"All query results exported to {OUT_DIR}/")