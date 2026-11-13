import sqlite3
from pathlib import Path

import streamlit as st


# The app.py file is inside the venv folder, while placements.db is in the
# project folder.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "placements.db"

STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def main():
    st.title("Placement Application Tracker")

    # Open a connection so the form can save and display application records.
    connection = sqlite3.connect("placements.db")

    try:
        # Collect the details for a new application.
        with st.form("add_application_form"):
            company_name = st.text_input("Company Name")
            job_role = st.text_input("Job Role")
            application_date = st.date_input("Application Date")
            status = st.selectbox("Status", STATUSES)
            submitted = st.form_submit_button("Add Application")

        # Check required fields before saving the application.
        if submitted:
            if not company_name.strip() or not job_role.strip():
                st.error("Company Name and Job Role cannot be empty.")
            else:
                connection.execute(
                    """
                    INSERT INTO applications
                        (company_name, job_role, application_date, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        company_name.strip(),
                        job_role.strip(),
                        application_date.isoformat(),
                        status,
                    ),
                )
                connection.commit()
                st.success("Application added successfully.")

        # Retrieve every application for the table and total count.
        applications = connection.execute(
            """
            SELECT application_id, company_name, job_role,
                   application_date, status
            FROM applications
            ORDER BY application_id
            """
        ).fetchall()

        st.header("Applications")
        if applications:
            application_rows = [
                {
                    "application_id": row[0],
                    "company_name": row[1],
                    "job_role": row[2],
                    "application_date": row[3],
                    "status": row[4],
                }
                for row in applications
            ]
            st.dataframe(application_rows, hide_index=True, use_container_width=True)
        else:
            st.info("No applications are available yet.")

        st.metric("Total Applications", len(applications))

        # Choose the most common role; alphabetical order breaks ties.
        most_applied_role = connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC, job_role COLLATE NOCASE ASC, job_role ASC
            LIMIT 1
            """
        ).fetchone()

        st.header("Most Applied Role")
        if most_applied_role:
            st.write(
                f"{most_applied_role[0]} "
                f"({most_applied_role[1]} application(s))"
            )
        else:
            st.info("There are no applications to summarize.")

        # Count each status, including statuses that currently have no records.
        rows_by_status = connection.execute(
            """
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            """
        ).fetchall()
        status_counts = {status_name: 0 for status_name in STATUSES}

        for status_name, count in rows_by_status:
            # Include any other status already stored in the database.
            display_status = status_name if status_name is not None else "Unspecified"
            status_counts[display_status] = count

        st.header("Status-wise Summary")
        for status_name, count in status_counts.items():
            st.write(f"**{status_name}:** {count}")

        st.bar_chart(
            {
                "Status": list(status_counts.keys()),
                "Applications": list(status_counts.values()),
            },
            x="Status",
            y="Applications",
        )
    finally:
        # Always close the database connection when the app finishes this run.
        connection.close()


if __name__ == "__main__":
    main()