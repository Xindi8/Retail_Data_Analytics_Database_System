import sqlite3
import pandas as pd

db_path = "data/store.db"
out_path = "store_export.xlsx"

conn = sqlite3.connect(db_path)

# find all tables
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
    conn
)["name"].tolist()

print("Tables found:", tables)

with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    for t in tables:
        df = pd.read_sql_query(f"SELECT * FROM {t};", conn)
        df.to_excel(writer, sheet_name=t[:31], index=False)

conn.close()
print(f"Exported to {out_path}")
