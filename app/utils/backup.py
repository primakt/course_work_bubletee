import subprocess
import os
from datetime import datetime
from config import DATABASE_URL

BACKUP_DIR = "backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

def create_pg_dump():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"teezy_backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    db_url_parts = DATABASE_URL.replace("postgresql+psycopg2://", "").split("@")
    user_pass = db_url_parts[0].split(":")
    host_db = db_url_parts[1].split("/")
    
    user = user_pass[0]
    password = user_pass[1]
    host = host_db[0]
    db_name = host_db[1]

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    command = [
        "pg_dump",
        "-h", host,
        "-U", user,
        "-d", db_name,
        "-F", "c",
        "-f", filepath
    ]

    result = subprocess.run(command, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Backup failed: {result.stderr}")
    
    return filepath