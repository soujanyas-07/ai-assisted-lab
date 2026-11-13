import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import initialize_database


class DatabaseMigrationTests(unittest.TestCase):
    def test_migration_adds_interview_date_and_preserves_existing_rows(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "placements.db"
            connection = sqlite3.connect(database_path)
            connection.execute(
                """
                CREATE TABLE applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_role TEXT NOT NULL,
                    application_date TEXT,
                    status TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT INTO applications
                    (company_name, job_role, application_date, status)
                VALUES (?, ?, ?, ?)
                """,
                ("Example Inc", "Engineer", "2026-01-01", "Applied"),
            )
            connection.commit()
            connection.close()

            initialize_database(database_path)
            initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(applications)")
            }
            application = connection.execute(
                """
                SELECT company_name, job_role, application_date, status, interview_date
                FROM applications
                """
            ).fetchone()
            connection.close()

            self.assertIn("interview_date", columns)
            self.assertEqual(
                application,
                ("Example Inc", "Engineer", "2026-01-01", "Applied", None),
            )

    def test_initialization_creates_application_table(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "new_placements.db"
            initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(applications)")
            }
            connection.close()

            self.assertIn("application_id", columns)
            self.assertIn("interview_date", columns)


if __name__ == "__main__":
    unittest.main()
