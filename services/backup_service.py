import os
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path
from config import BASE_DIR, BACKUPS_DIR, SQLITE_PATH, DUCKDB_PATH, UPLOADS_DIR, WORKSPACE_DIR

class BackupService:
    def create_backup(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"coding_practice_backup_{timestamp}.zip"
        backup_filepath = BACKUPS_DIR / backup_filename

        with zipfile.ZipFile(backup_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 1. Back up SQLite DB if exists
            if SQLITE_PATH.exists():
                zipf.write(SQLITE_PATH, arcname="database/app.db")
            
            # 2. Back up DuckDB if exists
            if DUCKDB_PATH.exists():
                zipf.write(DUCKDB_PATH, arcname="database/practice.duckdb")

            # 3. Back up Uploads
            for root, _, files in os.walk(UPLOADS_DIR):
                for file in files:
                    full_p = Path(root) / file
                    arc_p = Path("uploads") / full_p.relative_to(UPLOADS_DIR)
                    zipf.write(full_p, arcname=str(arc_p))

            # 4. Back up Workspace
            for root, _, files in os.walk(WORKSPACE_DIR):
                for file in files:
                    full_p = Path(root) / file
                    arc_p = Path("workspace") / full_p.relative_to(WORKSPACE_DIR)
                    zipf.write(full_p, arcname=str(arc_p))

            # Manifest
            manifest = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "app": "Coding Practice Hub"
            }
            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

        return backup_filepath

    def restore_backup(self, zip_filepath: Path) -> bool:
        if not zip_filepath.exists():
            return False

        temp_restore = BACKUPS_DIR / "temp_restore"
        if temp_restore.exists():
            shutil.rmtree(temp_restore)
        temp_restore.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_filepath, "r") as zipf:
                zipf.extractall(temp_restore)

            # Restore SQLite
            src_sqlite = temp_restore / "database" / "app.db"
            if src_sqlite.exists():
                shutil.copy2(src_sqlite, SQLITE_PATH)

            # Restore DuckDB
            src_duckdb = temp_restore / "database" / "practice.duckdb"
            if src_duckdb.exists():
                shutil.copy2(src_duckdb, DUCKDB_PATH)

            # Restore Uploads
            src_uploads = temp_restore / "uploads"
            if src_uploads.exists():
                for item in src_uploads.iterdir():
                    dst_item = UPLOADS_DIR / item.name
                    if item.is_dir():
                        if dst_item.exists():
                            shutil.rmtree(dst_item)
                        shutil.copytree(item, dst_item)
                    else:
                        shutil.copy2(item, dst_item)

            return True
        except Exception as e:
            print(f"Error during restore: {e}")
            return False
        finally:
            if temp_restore.exists():
                shutil.rmtree(temp_restore, ignore_errors=True)

backup_service = BackupService()
