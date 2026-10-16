import duckdb
import time
import os
import re
from pathlib import Path
from config import DUCKDB_PATH, SQLITE_PATH, CSV_UPLOADS, JSON_UPLOADS, PARQUET_UPLOADS, DATABASE_DIR
import sqlite3

USER_DBS_DIR = DATABASE_DIR / "user_dbs"
USER_DBS_DIR.mkdir(parents=True, exist_ok=True)

class DuckDBService:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DUCKDB_PATH)

    def get_connection(self):
        conn = duckdb.connect(self.db_path)
        
        # 1. Set file search path for uploads
        try:
            search_paths = f"{CSV_UPLOADS.as_posix()},{JSON_UPLOADS.as_posix()},{PARQUET_UPLOADS.as_posix()}"
            conn.execute(f"SET file_search_path='{search_paths}';")
        except Exception:
            pass

        # 2. Automatically attach all user-created databases
        try:
            for db_file in USER_DBS_DIR.glob("*.duckdb"):
                db_alias = db_file.stem
                # Don't attach if name conflicts with reserved keywords
                safe_alias = re.sub(r"[^a-zA-Z0-9_]", "_", db_alias).lower()
                try:
                    conn.execute(f"ATTACH IF NOT EXISTS '{db_file.as_posix()}' AS \"{safe_alias}\";")
                except Exception as e:
                    print(f"Error attaching {safe_alias}: {e}")
        except Exception as e:
            print(f"Error scanning user databases: {e}")

        return conn

    def list_databases(self):
        """Returns list of all available databases (main + attached user databases)."""
        dbs = [{"name": "main", "display_name": "practice (main / default)", "is_default": True}]
        for db_file in sorted(USER_DBS_DIR.glob("*.duckdb")):
            alias = re.sub(r"[^a-zA-Z0-9_]", "_", db_file.stem).lower()
            dbs.append({
                "name": alias,
                "display_name": alias,
                "filename": db_file.name,
                "size_kb": round(db_file.stat().st_size / 1024, 1),
                "is_default": False
            })
        return dbs

    def create_database(self, db_name: str) -> dict:
        """Creates a new DuckDB database file and attaches it."""
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", db_name.strip()).lower()
        if not clean_name:
            return {"success": False, "error": "Invalid database name"}
        if clean_name in ("main", "system", "temp"):
            return {"success": False, "error": f"'{clean_name}' is a reserved database name"}

        target_file = USER_DBS_DIR / f"{clean_name}.duckdb"
        try:
            # Initialize the database file
            init_conn = duckdb.connect(str(target_file))
            init_conn.execute("CREATE TABLE IF NOT EXISTS _info (created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            init_conn.close()

            # Attach to current connection
            conn = self.get_connection()
            conn.execute(f"ATTACH IF NOT EXISTS '{target_file.as_posix()}' AS \"{clean_name}\";")
            conn.close()

            return {
                "success": True,
                "database": clean_name,
                "filename": target_file.name,
                "message": f"Database '{clean_name}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

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

                # Register view for table_name
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{tbl}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception:
                    pass

                # Register view for original_name e.g. "sample_employees.csv"
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{orig_name}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception:
                    pass

                # Register view for clean_stem e.g. sample_employees
                try:
                    conn_duck.execute(f"CREATE OR REPLACE VIEW \"{clean_stem}\" AS SELECT * FROM {read_func}('{fpath}');")
                except Exception:
                    pass

            conn_duck.close()
        except Exception as e:
            print(f"Error syncing dataset views: {e}")

    def execute_query(self, query: str, active_db: str = "main", limit: int = 500) -> dict:
        start_time = time.time()
        conn = self.get_connection()
        result = {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "duration_ms": 0,
            "status": "SUCCESS",
            "error": None,
            "truncated": False,
            "active_database": active_db
        }

        # Auto-quote unquoted filename queries e.g. FROM sample_employees.csv -> FROM "sample_employees.csv"
        processed_query = re.sub(r"\bFROM\s+([a-zA-Z0-9_]+\.(?:csv|parquet|json))\b", r'FROM "\1"', query, flags=re.IGNORECASE)
        processed_query = re.sub(r"\bJOIN\s+([a-zA-Z0-9_]+\.(?:csv|parquet|json))\b", r'JOIN "\1"', processed_query, flags=re.IGNORECASE)

        try:
            # Set active database context if other than main
            if active_db and active_db.lower() != "main":
                try:
                    conn.execute(f"USE \"{active_db.lower()}\";")
                except Exception as e:
                    print(f"Could not switch to db {active_db}: {e}")

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
        """Inspect all databases, user tables, views, and columns across all attached databases."""
        conn = self.get_connection()
        schema_info = []

        try:
            # Get all databases
            dbs = conn.execute("SHOW DATABASES;").fetchall()
            db_names = [d[0] for d in dbs if d[0] not in ('system', 'temp')]

            for db in db_names:
                try:
                    tables = conn.execute(f"""
                        SELECT table_name, table_type 
                        FROM information_schema.tables 
                        WHERE table_catalog = '{db}' AND table_schema = 'main'
                        ORDER BY table_name;
                    """).fetchall()

                    for tbl, tbl_type in tables:
                        cols = conn.execute(f"""
                            SELECT column_name, data_type, character_maximum_length, is_nullable
                            FROM information_schema.columns 
                            WHERE table_catalog = '{db}' AND table_name = '{tbl}' AND table_schema = 'main'
                            ORDER BY ordinal_position;
                        """).fetchall()

                        cnt = None
                        try:
                            # If database is main, direct select, otherwise db.tbl
                            ref = f'"{tbl}"' if db == 'main' or db == 'practice' else f'"{db}"."{tbl}"'
                            cnt = conn.execute(f"SELECT count(*) FROM {ref}").fetchone()[0]
                        except Exception:
                            pass

                        formatted_cols = []
                        for c in cols:
                            c_name = c[0]
                            c_type = c[1] or ""
                            c_max_len = c[2]
                            c_null = c[3] or "YES"

                            # Calculate readable size
                            size_str = ""
                            type_upper = str(c_type).upper()
                            len_match = re.search(r"\((\d+)\)", type_upper)
                            if c_max_len:
                                size_str = f"max {c_max_len} chars"
                            elif len_match:
                                size_str = f"max {len_match.group(1)} chars"
                            elif "INT" in type_upper or "BIGINT" in type_upper:
                                size_str = "8 bytes" if "64" in type_upper or "BIG" in type_upper else "4 bytes"
                            elif "TINYINT" in type_upper:
                                size_str = "1 byte"
                            elif "SMALLINT" in type_upper:
                                size_str = "2 bytes"
                            elif "DOUBLE" in type_upper or "FLOAT" in type_upper or "REAL" in type_upper:
                                size_str = "8 bytes" if "DOUBLE" in type_upper else "4 bytes"
                            elif "DECIMAL" in type_upper or "NUMERIC" in type_upper:
                                size_str = "16 bytes"
                            elif "TIMESTAMP" in type_upper or "DATE" in type_upper or "TIME" in type_upper:
                                size_str = "8 bytes" if "TIMESTAMP" in type_upper else "4 bytes"
                            elif "BOOL" in type_upper:
                                size_str = "1 byte"
                            elif "VARCHAR" in type_upper or "TEXT" in type_upper:
                                size_str = "variable"
                            else:
                                size_str = "dynamic"

                            formatted_cols.append({
                                "name": c_name,
                                "type": c_type,
                                "size": size_str,
                                "nullable": c_null
                            })

                        schema_info.append({
                            "database": db,
                            "name": tbl,
                            "type": tbl_type,
                            "row_count": cnt,
                            "columns": formatted_cols,
                            "qualified_name": f"{db}.{tbl}" if db != 'main' else tbl
                        })
                except Exception as e:
                    print(f"Error inspecting db {db}: {e}")

        except Exception as e:
            print(f"Error exploring schema: {e}")
        finally:
            conn.close()

        return schema_info

    def get_databases_overview(self):
        """Returns overview of both SQLite and DuckDB databases (including user-created ones)."""
        overview = {
            "sqlite": {
                "name": "SQLite Application Database",
                "filename": "app.db",
                "path": str(SQLITE_PATH),
                "size_kb": round(SQLITE_PATH.stat().st_size / 1024, 1) if SQLITE_PATH.exists() else 0,
                "tables": []
            },
            "duckdb": {
                "name": "DuckDB Practice Database",
                "filename": "practice.duckdb",
                "path": str(DUCKDB_PATH),
                "size_kb": round(DUCKDB_PATH.stat().st_size / 1024, 1) if DUCKDB_PATH.exists() else 0,
                "databases_count": 1 + len(list(USER_DBS_DIR.glob("*.duckdb"))),
                "attached_dbs": self.list_databases(),
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

        # Query DuckDB views & tables across all attached databases
        try:
            schemas = self.get_explorer_schema()
            overview["duckdb"]["views"] = schemas
        except Exception as e:
            print(f"DuckDB overview error: {e}")

        return overview

duckdb_service = DuckDBService()
