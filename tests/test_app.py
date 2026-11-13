import csv
import io
import unittest

from app import applications_to_csv, filter_applications


class ApplicationHelpersTests(unittest.TestCase):
    def setUp(self):
        self.applications = [
            {
                "application_id": 1,
                "company_name": "Acme Corp",
                "job_role": "Engineer",
                "application_date": "2026-01-01",
                "status": "Applied",
                "interview_date": None,
            },
            {
                "application_id": 2,
                "company_name": "Example Inc",
                "job_role": "Analyst",
                "application_date": "2026-01-02",
                "status": "Interview Scheduled",
                "interview_date": "2026-02-01",
            },
            {
                "application_id": 3,
                "company_name": "Acme Labs",
                "job_role": "Designer",
                "application_date": "2026-01-03",
                "status": None,
                "interview_date": None,
            },
        ]

    def test_company_search_is_case_insensitive(self):
        matches = filter_applications(self.applications, "ACME")
        self.assertEqual(
            [application["application_id"] for application in matches],
            [1, 3],
        )

    def test_status_filter_can_be_combined_with_company_search(self):
        matches = filter_applications(
            self.applications, "acme", status_filter="Unspecified"
        )
        self.assertEqual(
            [application["application_id"] for application in matches],
            [3],
        )

    def test_csv_export_contains_header_and_selected_records(self):
        selected = filter_applications(
            self.applications, status_filter="Interview Scheduled"
        )
        exported = applications_to_csv(selected).decode("utf-8-sig")
        records = list(csv.reader(io.StringIO(exported)))

        self.assertEqual(
            records[0],
            [
                "application_id",
                "company_name",
                "job_role",
                "application_date",
                "status",
                "interview_date",
            ],
        )
        self.assertEqual(records[1][1], "Example Inc")
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
