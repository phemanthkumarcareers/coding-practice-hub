import duckdb
import time
from pathlib import Path
from config import DUCKDB_PATH, SQLITE_PATH
import sqlite3

class DuckDBService:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DUCKDB_PATH)

    def get_connection(self):
        return duckdb.connect(self.db_path)

    def sync_dataset_views(self):
        """Automatically create views in DuckDB for all uploaded datasets."""
        try:
            conn_sqlite = sqlite3.connect(SQLITE_PATH)
            conn_sqlite.row_factory = sqlite3.Row
            datasets = conn_sqlite.execute("SELECT table_name, file_path, file_type FROM datasets").fetchall()
            conn_sqlite.close()

            if not datasets:
                return

            conn_duck = self.get_connection()
            for ds in datasets:
                tbl = ds["table_name"]
                fpath = Path(ds["file_path"]).as_posix()
                ftype = ds["file_type"].lower()

                try:
                    if ftype == "csv":
                        conn_duck.execute(f"CREATE OR REPLACE VIEW \"{tbl}\" AS SELECT * FROM read_csv_auto('{fpath}');")
                    elif ftype == "parquet":
                        conn_duck.execute(f"CREATE OR REPLACE VIEW \"{tbl}\" AS SELECT * FROM read_parquet('{fpath}');")
                    elif ftype == "json":
                        conn_duck.execute(f"CREATE OR REPLACE VIEW \"{tbl}\" AS SELECT * FROM read_json_auto('{fpath}');")
                except Exception as e:
                    print(f"Error registering DuckDB view for {tbl}: {e}")
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

        try:
            # DuckDB allows multiple statements if executed properly or single query
            # We execute query and fetch results
            rel = conn.sql(query)
            if rel is not None:
                columns = rel.columns
                result["columns"] = columns
                
                # Fetch limited rows to prevent browser freeze on massive tables
                fetched = rel.fetchmany(limit + 1)
                if len(fetched) > limit:
                    result["truncated"] = True
                    fetched = fetched[:limit]
                
                # Convert rows to JSON-serializable types
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

                # Get row count estimate if possible
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

duckdb_service = DuckDBService()
