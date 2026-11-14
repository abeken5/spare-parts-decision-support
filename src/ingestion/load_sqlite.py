from pathlib import Path
import sqlite3
import pandas as pd


def build_sqlite_db(
    raw_dir: str = "data/raw",
    sql_dir: str = "sql",
    db_path: str = "data/processed/mro_inventory.db",
) -> Path:
    """Create SQLite database, load raw CSVs, and materialize analytical SQL views."""
    raw_path = Path(raw_dir)
    sql_path = Path(sql_dir)
    out_db = Path(db_path)
    out_db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(out_db) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript((sql_path / "schema.sql").read_text(encoding="utf-8"))

        for table in ["parts", "demand_history", "lead_time_history", "current_policy"]:
            df = pd.read_csv(raw_path / f"{table}.csv")
            df.to_sql(table, conn, if_exists="append", index=False)

        conn.executescript((sql_path / "abc_analysis.sql").read_text(encoding="utf-8"))
        conn.executescript((sql_path / "kpi_views.sql").read_text(encoding="utf-8"))

        summary = pd.read_sql_query(
            """
            SELECT
                abc_class,
                COUNT(*) AS part_count,
                ROUND(SUM(annual_usage_value), 2) AS total_annual_value_tl,
                ROUND(AVG(avg_lead_time_days), 1) AS mean_lt_days
            FROM vw_part_kpis
            GROUP BY abc_class
            ORDER BY abc_class;
            """,
            conn,
        )
        print("SQLite veritabani hazir:", out_db)
        print("\nSQL ABC Analizi Ozeti (Ilk 24 Ay Kalibrasyon):")
        print(summary.to_string(index=False))

    return out_db


if __name__ == "__main__":
    build_sqlite_db()
