import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "placements.db"


def initialize_database(database_path=None):
    if database_path is None:
        database_path = DATABASE_PATH

    connection = sqlite3.connect(database_path)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT,
                interview_date TEXT
            )
            """
        )

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(applications)")
        }
        if "interview_date" not in columns:
            connection.execute(
                "ALTER TABLE applications ADD COLUMN interview_date TEXT"
            )

        connection.commit()
    finally:
        connection.close()
