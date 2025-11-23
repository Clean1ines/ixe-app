import os
import sqlite3

DB_PATH = "test_data/fipi_data.db"
ASSETS_DIR = "test_data/assets"

def verify_asset_records():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT asset_url, file_path, download_status FROM assets WHERE download_status = 1")
    rows = cur.fetchall()
    conn.close()

    for url, path, status in rows:
        full_path = os.path.join(ASSETS_DIR, os.path.basename(path))
        exists = os.path.exists(full_path)
        print(f"URL: {url}")
        print(f"Expected path: {full_path}")
        print(f"File exists: {exists}")
        print(f"DB status: {status}")
        print("-" * 50)

if __name__ == "__main__":
    verify_asset_records()
