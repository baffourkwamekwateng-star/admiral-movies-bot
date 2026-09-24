"""
Optional CSV importer.

Use this only for authorized content.

CSV columns:
message_id,file_id,title,file_name

Example:
12345,BAACAg...,Avatar 2009,Avatar.2009.1080p.mkv

Run:
    python import_movies.py movies.csv
"""

import csv
import sys
import sqlite3
from bot import DATABASE, normalize, init_db

def main():
    if len(sys.argv) != 2:
        print("Usage: python import_movies.py movies.csv")
        raise SystemExit(1)

    init_db()
    filename = sys.argv[1]

    with sqlite3.connect(DATABASE) as conn, open(
        filename, newline="", encoding="utf-8"
    ) as f:
        reader = csv.DictReader(f)

        required = {"message_id", "file_id", "title", "file_name"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                "CSV must contain: message_id,file_id,title,file_name"
            )

        for row in reader:
            conn.execute(
                """
                INSERT OR REPLACE INTO movies
                (message_id, file_id, title, normalized_title, file_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    int(row["message_id"]),
                    row["file_id"],
                    row["title"],
                    normalize(row["title"]),
                    row["file_name"],
                ),
            )

        conn.commit()

    print("Import completed.")

if __name__ == "__main__":
    main()
