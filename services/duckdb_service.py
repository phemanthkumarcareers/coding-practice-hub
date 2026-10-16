import duckdb
import time
import os
import re
from pathlib import Path
from config import DUCKDB_PATH, SQLITE_PATH, CSV_UPLOADS, JSON_UPLOADS, PARQUET_UPLOADS
import sqlite3

class DuckDBService:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DUCKDB_PATH)

    def get_connection(self):
        conn = duckdb.connect(self.db_path)
        # Set file search path so files in uploads can be queried by relative filename directly
        try:
            search_paths = f"{CSV_UPLOADS.as_posix()},{JSON_UPLOADS.as_posix()},{PARQUET_UPLOADS.as_posix()}"
            conn.execute(f"SET file_search_path='{search_paths}';")
        except Exception:
            pass
        return conn

    def sync_dataset_views(self):
        """Automatically create views in DuckDB for all uploaded datasets."""
        try:
            conn_sqlite = sqlite3.connect(SQLITE_PATH)
            conn_sqlite.row_factory = sqlite3.Row
            datasets = conn_sqlite.execute("SELECT table_name, original_name, file_path, file_type FROM datasets").fetchall()
            conn_sqlite.close()

            if not datasets:
                return

            conn_duck = self.get_connection()
            for ds in datasets:
                tbl = ds["table_name"]
                orig_name = ds["original_name"]
                stem_name = Path(orig_name).stem
                clean_stem = re.sub(r"[^a-zA-Z0-9_]", "_", stem_name).lower()
                fpath = Path(ds["file_path"]).as_posix()
                ftype = ds["file_type"].lower()

                read_func = "read_csv_auto" if ftype == "csv" else ("read_parquet" if ftype == "parquet" else "read_json_auto")

                # Register primary table_name view
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{tbl}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception as e:
                    print(f"Error registering view {tbl}: {e}")

                # Register original file name view e.g. "sales.csv"
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{orig_name}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception:
                    pass

                # Register bare stem view e.g. sales
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{clean_stem}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception:
                    pass

            conn_duck.close()
        except Exception as e:
            print(f"Error syncing dataset views: {e}")

    def execute_query(self, query, limit=500):
        start_time = time.time()
        conn = self.get_connection()
        result = {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "duration_ms": 0,
            "status": "SUCCESS",
            "error": None,
            "truncated": False
        }

        # Auto-quote unquoted filename queries e.g. FROM sample_employees.csv -> FROM "sample_employees.csv"
        # DuckDB interprets unquoted . as schema.table
        processed_query = re.sub(r"\bFROM\s+([a-zA-Z0-9_]+\.(?:csv|parquet|json))\b", r'FROM "\1"', query, flags=re.IGNORECASE)
        processed_query = re.sub(r"\bJOIN\s+([a-zA-Z0-9_]+\.(?:csv|parquet|json))\b", r'JOIN "\1"', processed_query, flags=re.IGNORECASE)

        try:
            rel = conn.sql(processed_query)
            if rel is not None:
                columns = rel.columns
                result["columns"] = columns

                fetched = rel.fetchmany(limit + 1)
                if len(fetched) > limit:
                    result["truncated"] = True
                    fetched = fetched[:limit]

                serializable_rows = []
                for row in fetched:
                    row_list = []
                    for item in row:
                        if item is None:
                            row_list.append(None)
                        elif isinstance(item, (int, float, bool, str)):
                            row_list.append(item)
                        else:
                            row_list.append(str(item))
                    serializable_rows.append(row_list)

                result["rows"] = serializable_rows
                result["row_count"] = len(serializable_rows)
            else:
                result["columns"] = ["Result"]
                result["rows"] = [["Command executed successfully."]]
                result["row_count"] = 1
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
        finally:
            result["duration_ms"] = int((time.time() - start_time) * 1000)
            conn.close()

        return result

    def get_explorer_schema(self):
        """Inspect DuckDB tables, views, and schemas for the table explorer."""
        conn = self.get_connection()
        schema_info = []
        try:
            tables_rel = conn.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                ORDER BY table_name;
            """).fetchall()

            for tbl, tbl_type in tables_rel:
                cols_rel = conn.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{tbl}' AND table_schema = 'main'
                    ORDER BY ordinal_position;
                """).fetchall()

                count = None
                try:
                    count = conn.execute(f"SELECT count(*) FROM \"{tbl}\"").fetchone()[0]
                except Exception:
                    pass

                schema_info.append({
                    "name": tbl,
                    "type": tbl_type,
                    "row_count": count,
                    "columns": [{"name": c[0], "type": c[1]} for c in cols_rel]
                })
        except Exception as e:
            print(f"Error exploring schema: {e}")
        finally:
            conn.close()

        return schema_info

    def get_databases_overview(self):
        """Returns overview of both SQLite and DuckDB databases."""
        overview = {
            "sqlite": {
                "name": "SQLite Application Database",
                "filename": "app.db",
                "path": str(SQLITE_PATH),
                "size_kb": round(SQLITE_PATH.stat().st_size / 1024, 1) if SQLITE_PATH.exists() else 0,
                "tables": []
            },
            "duckdb": {
                "name": "DuckDB Analytical Practice Database",
                "filename": "practice.duckdb",
                "path": str(DUCKDB_PATH),
                "size_kb": round(DUCKDB_PATH.stat().st_size / 1024, 1) if DUCKDB_PATH.exists() else 0,
                "views": []
            }
        }

        # Query SQLite tables & counts
        try:
            conn_sq = sqlite3.connect(SQLITE_PATH)
            conn_sq.row_factory = sqlite3.Row
            tbls = conn_sq.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            for t in tbls:
                t_name = t["name"]
                cnt = conn_sq.execute(f"SELECT count(*) FROM \"{t_name}\"").fetchone()[0]
                overview["sqlite"]["tables"].append({"name": t_name, "count": cnt})
            conn_sq.close()
        except Exception as e:
            print(f"SQLite overview error: {e}")

        # Query DuckDB views & counts
        try:
            conn_dk = self.get_connection()
            views = conn_dk.execute("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema='main'").fetchall()
            for v_name, v_type in views:
                cnt = None
                try:
                    cnt = conn_dk.execute(f"SELECT count(*) FROM \"{v_name}\"").fetchone()[0]
                except Exception:
                    pass
                overview["duckdb"]["views"].append({"name": v_name, "type": v_type, "count": cnt})
            conn_dk.close()
        except Exception as e:
            print(f"DuckDB overview error: {e}")

        return overview

duckdb_service = DuckDBService()
