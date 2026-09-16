"""
src/bi/export_powerbi.py

Exports data from the Retail Data Analytics Database into a star-schema
(dimension tables + fact tables) as a set of CSV files, ready to be
loaded into Power BI.

Design principles:
    - Connects to the database in read-only mode (mode=ro), so this
      script can never modify any business data.
    - Does not depend on or modify the existing db/repository.py,
      to avoid touching the existing business logic in any way.
    - Each table is exported as its own CSV file, so Power BI can
      import all of them at once via a "Folder" data source, and it
      also makes it easy to wire up Power BI's Scheduled Refresh later.

Usage:
    python -m src.bi.export_powerbi data/store.db
    python -m src.bi.export_powerbi data/store.db data/powerbi_export
"""

import sys
import os
import csv
import sqlite3
import datetime as dt


# ------------------------------------------------------------------ #
#  Helper functions
# ------------------------------------------------------------------ #

def connect_readonly(db_path: str) -> sqlite3.Connection:
    """Open the database in read-only mode to avoid any write risk."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def write_csv(path: str, rows, headers: list) -> None:
    """Write a list of sqlite3.Row or dict objects to a CSV file using the given headers."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow([r[h] for h in headers])


# ------------------------------------------------------------------ #
#  Dimension Tables
# ------------------------------------------------------------------ #

def export_dim_products(conn, outdir):
    rows = conn.execute(
        "SELECT pid, name, category, price, stock_count, descr FROM products;"
    ).fetchall()
    headers = ["pid", "name", "category", "price", "stock_count", "descr"]
    write_csv(os.path.join(outdir, "dim_products.csv"), rows, headers)
    print(f"[OK] dim_products.csv        ({len(rows)} rows)")


def export_dim_customers(conn, outdir):
    rows = conn.execute("SELECT cid, name, email FROM customers;").fetchall()
    headers = ["cid", "name", "email"]
    write_csv(os.path.join(outdir, "dim_customers.csv"), rows, headers)
    print(f"[OK] dim_customers.csv       ({len(rows)} rows)")


def export_dim_date(conn, outdir):
    """
    Builds a continuous date dimension table by collecting every date
    that appears in orders / sessions / search / viewedProduct, so that
    Power BI can aggregate metrics by week / month / weekday.
    """
    dates = set()
    sources = [
        ("orders", "odate"),
        ("sessions", "start_time"),
        ("search", "ts"),
        ("viewedProduct", "ts"),
    ]
    for table, col in sources:
        try:
            rows = conn.execute(
                f"SELECT {col} FROM {table} WHERE {col} IS NOT NULL;"
            ).fetchall()
        except sqlite3.Error:
            continue
        for r in rows:
            try:
                dates.add(dt.datetime.strptime(r[0][:10], "%Y-%m-%d").date())
            except Exception:
                pass

    if not dates:
        print("[!!] No dates found in the database, skipping dim_date.csv")
        return

    start, end = min(dates), max(dates)
    headers = ["date", "year", "month", "day", "week", "weekday_name", "is_weekend"]
    out_rows = []
    cur = start
    while cur <= end:
        out_rows.append({
            "date": cur.isoformat(),
            "year": cur.year,
            "month": cur.month,
            "day": cur.day,
            "week": cur.isocalendar()[1],
            "weekday_name": cur.strftime("%A"),
            "is_weekend": cur.weekday() >= 5,
        })
        cur += dt.timedelta(days=1)

    with open(os.path.join(outdir, "dim_date.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for d in out_rows:
            w.writerow([d[h] for h in headers])
    print(f"[OK] dim_date.csv            ({len(out_rows)} rows, {start} ~ {end})")


# ------------------------------------------------------------------ #
#  Fact Tables
# ------------------------------------------------------------------ #

def export_fact_orders(conn, outdir):
    rows = conn.execute(
        """
        SELECT o.ono, o.cid, o.sessionNo, o.odate, o.shipping_address,
               COALESCE(SUM(ol.qty * ol.uprice), 0) AS order_total
        FROM orders o
        LEFT JOIN orderlines ol ON o.ono = ol.ono
        GROUP BY o.ono, o.cid, o.sessionNo, o.odate, o.shipping_address;
        """
    ).fetchall()
    headers = ["ono", "cid", "sessionNo", "odate", "shipping_address", "order_total"]
    write_csv(os.path.join(outdir, "fact_orders.csv"), rows, headers)
    print(f"[OK] fact_orders.csv         ({len(rows)} rows)")


def export_fact_orderlines(conn, outdir):
    """
    Order line items - this is the core table for analyzing "which
    products sell well" and "what makes up total revenue".
    cid / odate are included here so Power BI can aggregate directly
    without needing an extra relationship hop.
    """
    rows = conn.execute(
        """
        SELECT ol.ono, ol.lineNo, ol.pid, ol.qty, ol.uprice,
               (ol.qty * ol.uprice) AS line_total,
               o.cid, o.odate
        FROM orderlines ol
        JOIN orders o ON o.ono = ol.ono;
        """
    ).fetchall()
    headers = ["ono", "lineNo", "pid", "qty", "uprice", "line_total", "cid", "odate"]
    write_csv(os.path.join(outdir, "fact_orderlines.csv"), rows, headers)
    print(f"[OK] fact_orderlines.csv     ({len(rows)} rows)")


def export_fact_views(conn, outdir):
    rows = conn.execute("SELECT cid, sessionNo, ts, pid FROM viewedProduct;").fetchall()
    headers = ["cid", "sessionNo", "ts", "pid"]
    write_csv(os.path.join(outdir, "fact_views.csv"), rows, headers)
    print(f"[OK] fact_views.csv          ({len(rows)} rows)")


def export_fact_search(conn, outdir):
    rows = conn.execute("SELECT cid, sessionNo, ts, query FROM search;").fetchall()
    headers = ["cid", "sessionNo", "ts", "query"]
    write_csv(os.path.join(outdir, "fact_search.csv"), rows, headers)
    print(f"[OK] fact_search.csv         ({len(rows)} rows)")


def export_fact_sessions(conn, outdir):
    """
    Session records, with an extra duration_minutes column computed
    on the Python side (rather than in SQL) because end_time can be
    NULL for sessions the user never logged out of.
    """
    rows = conn.execute(
        "SELECT cid, sessionNo, start_time, end_time FROM sessions;"
    ).fetchall()

    headers = ["cid", "sessionNo", "start_time", "end_time", "duration_minutes"]
    out_rows = []
    for r in rows:
        d = dict(r)
        d["duration_minutes"] = None
        if d.get("end_time"):
            try:
                t1 = dt.datetime.strptime(d["start_time"], "%Y-%m-%d %H:%M:%S")
                t2 = dt.datetime.strptime(d["end_time"], "%Y-%m-%d %H:%M:%S")
                d["duration_minutes"] = round((t2 - t1).total_seconds() / 60, 1)
            except Exception:
                pass
        out_rows.append(d)

    with open(os.path.join(outdir, "fact_sessions.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for d in out_rows:
            w.writerow([d[h] for h in headers])
    print(f"[OK] fact_sessions.csv       ({len(out_rows)} rows)")


# ------------------------------------------------------------------ #
#  Main entry point
# ------------------------------------------------------------------ #

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.bi.export_powerbi <db_path> [output_dir]")
        sys.exit(1)

    db_path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "data/powerbi_export"

    if not os.path.exists(db_path):
        print(f"[X] Database file not found: {db_path}")
        sys.exit(1)

    os.makedirs(outdir, exist_ok=True)

    conn = connect_readonly(db_path)
    print(f">>> Exporting from {db_path} to {outdir} ...\n")
    try:
        # Dimension tables
        export_dim_products(conn, outdir)
        export_dim_customers(conn, outdir)
        export_dim_date(conn, outdir)
        # Fact tables
        export_fact_orders(conn, outdir)
        export_fact_orderlines(conn, outdir)
        export_fact_views(conn, outdir)
        export_fact_search(conn, outdir)
        export_fact_sessions(conn, outdir)
    finally:
        conn.close()

    print(f"\n[DONE] All tables exported to: {outdir}")
    print("Next step: open Power BI Desktop -> Get Data -> Folder -> select this directory to import all CSVs,")


if __name__ == "__main__":
    main()