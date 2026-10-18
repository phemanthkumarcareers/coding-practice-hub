import os
import shutil
import zipfile
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from config import (
    BASE_DIR,
    BACKUPS_DIR,
    DATABASE_DIR,
    SQLITE_PATH,
    DUCKDB_PATH,
    UPLOADS_DIR,
    CSV_UPLOADS,
    JSON_UPLOADS,
    PARQUET_UPLOADS,
    WORKSPACE_DIR,
    detect_java_home,
    detect_spark_home
)

USER_DBS_DIR = DATABASE_DIR / "user_dbs"

class BackupService:
    def _get_sqlite_path(self) -> Path:
        return Path(os.environ.get("CODING_HUB_DB_PATH") or SQLITE_PATH)

    def create_backup(self, custom_filename: str = None) -> Path:
        """
        Creates a complete replica backup archive of the entire application:
        - SQLite database (dashboard sessions, daily practices, executions, notes/documentation, settings, datasets)
        - DuckDB database & user-created databases
        - All uploaded dataset files (csv, parquet, json)
        - All multi-file project workspace directories and code
        - Manifest with full table and file verification counts
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = custom_filename or f"coding_practice_backup_{timestamp}.zip"
        backup_filepath = BACKUPS_DIR / backup_filename
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        temp_dir = BACKUPS_DIR / f"temp_snap_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_sqlite_snap = temp_dir / "app_snapshot.db"

        try:
            # 1. Safely snapshot SQLite DB via native online backup (flushes WAL & avoids Windows file locking)
            db_counts = {}
            sqlite_target = self._get_sqlite_path()
            if sqlite_target.exists():
                src_conn = sqlite3.connect(sqlite_target)
                src_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                dest_conn = sqlite3.connect(temp_sqlite_snap)
                src_conn.backup(dest_conn)
                dest_conn.close()

                # Gather table counts for manifest
                cursor = src_conn.cursor()
                tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
                for tbl in tables:
                    try:
                        db_counts[tbl] = cursor.execute(f"SELECT COUNT(*) FROM \"{tbl}\"").fetchone()[0]
                    except Exception:
                        pass
                src_conn.close()

            # 2. Checkpoint DuckDB if exists to flush WAL into database files
            if DUCKDB_PATH.exists():
                try:
                    import duckdb
                    dconn = duckdb.connect(str(DUCKDB_PATH))
                    dconn.execute("CHECKPOINT;")
                    dconn.close()
                except Exception as ex:
                    print(f"Notice: DuckDB checkpoint: {ex}")

            # 3. Build Zip Archive
            with zipfile.ZipFile(backup_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add SQLite snapshot
                if temp_sqlite_snap.exists():
                    zipf.write(temp_sqlite_snap, arcname="database/app.db")

                # Add DuckDB database
                if DUCKDB_PATH.exists():
                    zipf.write(DUCKDB_PATH, arcname="database/practice.duckdb")

                # Add all user-created DuckDB databases
                if USER_DBS_DIR.exists():
                    for db_file in USER_DBS_DIR.glob("*.duckdb"):
                        arcname = f"database/user_dbs/{db_file.name}"
                        zipf.write(db_file, arcname=arcname)

                # Add all uploaded datasets (csv, json, parquet, etc.)
                uploads_count = 0
                if UPLOADS_DIR.exists():
                    for root, _, files in os.walk(UPLOADS_DIR):
                        for file in files:
                            full_p = Path(root) / file
                            # Skip temporary files
                            if file.endswith(".tmp") or file.endswith(".lock"):
                                continue
                            arc_p = Path("uploads") / full_p.relative_to(UPLOADS_DIR)
                            zipf.write(full_p, arcname=str(arc_p))
                            uploads_count += 1

                # Add all workspace projects, multi-file code, and templates
                workspace_count = 0
                if WORKSPACE_DIR.exists():
                    for root, _, files in os.walk(WORKSPACE_DIR):
                        for file in files:
                            full_p = Path(root) / file
                            if file.endswith(".tmp") or file.endswith(".lock"):
                                continue
                            arc_p = Path("workspace") / full_p.relative_to(WORKSPACE_DIR)
                            zipf.write(full_p, arcname=str(arc_p))
                            workspace_count += 1

                # Create comprehensive replica manifest
                manifest = {
                    "created_at": datetime.now().isoformat(),
                    "version": "2.0",
                    "manifest_version": "2.0",
                    "app": "Coding Practice Hub",
                    "platform": sys.platform,
                    "table_counts": db_counts,
                    "stats": {
                        "daily_sessions": db_counts.get("daily_sessions", 0),
                        "practices": db_counts.get("practices", 0),
                        "executions": db_counts.get("executions", 0),
                        "notes_documents": db_counts.get("key_notes", 0),
                        "datasets": db_counts.get("datasets", 0),
                        "settings": db_counts.get("settings", 0),
                        "uploaded_files": uploads_count,
                        "workspace_files": workspace_count
                    }
                }
                zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

            return backup_filepath
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def restore_backup(self, zip_filepath: Path) -> dict:
        """
        Restores a backup archive into the active application as an exact replica.
        Ensures compatibility across different computers and directories.
        """
        if not zip_filepath.exists():
            return {"success": False, "error": f"Backup file '{zip_filepath}' not found."}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_restore = BACKUPS_DIR / f"temp_restore_{timestamp}"
        if temp_restore.exists():
            shutil.rmtree(temp_restore, ignore_errors=True)
        temp_restore.mkdir(parents=True, exist_ok=True)

        result = {
            "success": False,
            "message": "",
            "stats": {}
        }

        try:
            # 1. Extract zip archive
            with zipfile.ZipFile(zip_filepath, "r") as zipf:
                zipf.extractall(temp_restore)

            manifest = {}
            manifest_file = temp_restore / "manifest.json"
            if manifest_file.exists():
                try:
                    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                    result["stats"] = manifest.get("stats", {})
                except Exception:
                    pass

            # 2. Stop running PySpark session so files aren't held open
            try:
                from services.pyspark_service import pyspark_service
                pyspark_service.restart_session()
            except Exception:
                pass

            # 3. Restore SQLite database safely via online backup
            src_sqlite = temp_restore / "database" / "app.db"
            sqlite_target = self._get_sqlite_path()
            if src_sqlite.exists():
                sqlite_target.parent.mkdir(parents=True, exist_ok=True)
                src_conn = sqlite3.connect(src_sqlite)
                dest_conn = sqlite3.connect(sqlite_target)
                src_conn.backup(dest_conn)
                src_conn.close()

                # Re-align dataset file paths for the current machine
                dest_cursor = dest_conn.cursor()
                try:
                    dataset_rows = dest_cursor.execute("SELECT id, file_name, file_type, file_path FROM datasets").fetchall()
                    for d_id, f_name, f_type, old_path in dataset_rows:
                        # Compute expected path in local UPLOADS_DIR
                        expected_path = UPLOADS_DIR / f_type.lower() / f_name
                        if not expected_path.exists():
                            # Fallback search anywhere in UPLOADS_DIR
                            found = list(UPLOADS_DIR.rglob(f_name))
                            if found:
                                expected_path = found[0]
                            else:
                                expected_path = UPLOADS_DIR / f_name

                        dest_cursor.execute(
                            "UPDATE datasets SET file_path = ? WHERE id = ?",
                            (str(expected_path), d_id)
                        )
                    dest_conn.commit()
                except Exception as e:
                    print(f"Notice: Dataset path realignment: {e}")

                # Ensure system-specific settings (python, java, spark) match current machine
                try:
                    settings_dict = dict(dest_cursor.execute("SELECT key, value FROM settings").fetchall())
                    
                    # Validate python executable
                    py_path = settings_dict.get("python_executable", "")
                    if not py_path or not Path(py_path).exists():
                        dest_cursor.execute("UPDATE settings SET value = ? WHERE key = 'python_executable'", (sys.executable,))
                    
                    # Validate java_home
                    j_home = settings_dict.get("java_home", "")
                    if not j_home or not Path(j_home).exists():
                        detected_java = detect_java_home()
                        if detected_java:
                            dest_cursor.execute("UPDATE settings SET value = ? WHERE key = 'java_home'", (detected_java,))
                    
                    # Validate spark_home
                    s_home = settings_dict.get("spark_home", "")
                    if not s_home or not Path(s_home).exists():
                        detected_spark = detect_spark_home()
                        if detected_spark:
                            dest_cursor.execute("UPDATE settings SET value = ? WHERE key = 'spark_home'", (detected_spark,))
                    
                    dest_conn.commit()
                except Exception as e:
                    print(f"Notice: Settings adaptation for current host: {e}")

                dest_conn.close()

            # 4. Restore DuckDB Databases
            src_duckdb = temp_restore / "database" / "practice.duckdb"
            if src_duckdb.exists():
                try:
                    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_duckdb, DUCKDB_PATH)
                except Exception as e:
                    print(f"Notice: copying practice.duckdb: {e}")

            src_user_dbs = temp_restore / "database" / "user_dbs"
            if src_user_dbs.exists():
                USER_DBS_DIR.mkdir(parents=True, exist_ok=True)
                for db_file in src_user_dbs.glob("*.duckdb"):
                    try:
                        shutil.copy2(db_file, USER_DBS_DIR / db_file.name)
                    except Exception as e:
                        print(f"Notice: copying user db {db_file.name}: {e}")

            # 5. Restore Uploaded Dataset Files
            src_uploads = temp_restore / "uploads"
            if src_uploads.exists():
                UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                for item in src_uploads.iterdir():
                    dst_item = UPLOADS_DIR / item.name
                    if item.is_dir():
                        if dst_item.exists():
                            shutil.rmtree(dst_item, ignore_errors=True)
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dst_item)

            # 6. Restore Workspace Directories & Project Files
            src_workspace = temp_restore / "workspace"
            if src_workspace.exists():
                WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
                for item in src_workspace.iterdir():
                    dst_item = WORKSPACE_DIR / item.name
                    if item.is_dir():
                        shutil.copytree(item, dst_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dst_item)

            # 7. Re-sync DuckDB Views with restored datasets
            try:
                from services.duckdb_service import duckdb_service
                duckdb_service.sync_dataset_views()
            except Exception as e:
                print(f"Notice: sync_dataset_views after restore: {e}")

            # Count restored items for user feedback
            final_conn = sqlite3.connect(sqlite_target)
            s_cnt = final_conn.execute("SELECT COUNT(*) FROM daily_sessions").fetchone()[0]
            p_cnt = final_conn.execute("SELECT COUNT(*) FROM practices").fetchone()[0]
            n_cnt = final_conn.execute("SELECT COUNT(*) FROM key_notes").fetchone()[0]
            d_cnt = final_conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
            final_conn.close()

            result["success"] = True
            result["message"] = (
                f"Replica restored successfully! "
                f"{s_cnt} daily sessions, {p_cnt} practices, {n_cnt} notes/documentation documents, "
                f"{d_cnt} datasets, and all workspace files restored."
            )
            result["counts"] = {
                "daily_sessions": s_cnt,
                "practices": p_cnt,
                "notes": n_cnt,
                "datasets": d_cnt
            }
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"Error during restore: {str(e)}"}
        finally:
            if temp_restore.exists():
                shutil.rmtree(temp_restore, ignore_errors=True)

backup_service = BackupService()
