import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import database
from streamlit.testing.v1 import AppTest


class ApplicationUITests(unittest.TestCase):
    def test_edit_interview_and_status_and_confirm_deletion(self):
        original_database_path = database.DATABASE_PATH

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "placements.db"
            database.initialize_database(database_path)
            connection = sqlite3.connect(database_path)
            connection.executemany(
                """
                INSERT INTO applications
                    (company_name, job_role, application_date, status, interview_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        "TestCo",
                        "Analyst",
                        date.today().isoformat(),
                        "Applied",
                        (date.today() + timedelta(days=5)).isoformat(),
                    ),
                    (
                        "OtherCo",
                        "Developer",
                        date.today().isoformat(),
                        "Applied",
                        None,
                    ),
                ],
            )
            connection.commit()
            connection.close()

            database.DATABASE_PATH = database_path
            try:
                app = AppTest.from_file(
                    str(Path(__file__).resolve().parents[1] / "app.py"),
                    default_timeout=20,
                ).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.dataframe), 2)

                app.text_input[2].set_value("testco").run()
                self.assertEqual(
                    sum(button.label == "Delete application" for button in app.button),
                    1,
                )
                app.text_input[2].set_value("").run()

                updated_interview_date = date.today() + timedelta(days=10)
                app.selectbox[2].select("Shortlisted")
                app.date_input[1].set_value(updated_interview_date)
                next(
                    button for button in app.button if button.label == "Save changes"
                ).click().run()

                connection = sqlite3.connect(database_path)
                updated_application = connection.execute(
                    """
                    SELECT status, interview_date
                    FROM applications
                    WHERE company_name = 'TestCo'
                    """
                ).fetchone()
                connection.close()
                self.assertEqual(
                    updated_application,
                    ("Shortlisted", updated_interview_date.isoformat()),
                )

                next(
                    button
                    for button in app.button
                    if button.label == "Delete application"
                ).click().run()
                next(
                    button for button in app.button if button.label == "Cancel"
                ).click().run()

                connection = sqlite3.connect(database_path)
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM applications WHERE company_name = 'TestCo'"
                    ).fetchone()[0],
                    1,
                )
                connection.close()

                next(
                    button
                    for button in app.button
                    if button.label == "Delete application"
                ).click().run()
                next(
                    button
                    for button in app.button
                    if button.label == "Confirm deletion"
                ).click().run()

                connection = sqlite3.connect(database_path)
                remaining_count = connection.execute(
                    "SELECT COUNT(*) FROM applications"
                ).fetchone()[0]
                connection.close()
                self.assertEqual(remaining_count, 1)
                self.assertFalse(app.exception)
            finally:
                database.DATABASE_PATH = original_database_path


if __name__ == "__main__":
    unittest.main()
