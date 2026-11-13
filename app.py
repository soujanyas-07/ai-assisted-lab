import csv
import io
import sqlite3
from datetime import date

import streamlit as st

from database import DATABASE_PATH, initialize_database


STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]
APPLICATION_COLUMNS = [
    "application_id",
    "company_name",
    "job_role",
    "application_date",
    "status",
    "interview_date",
]


def filter_applications(applications, company_query="", status_filter="All statuses"):
    query = company_query.strip().casefold()
    return [
        application
        for application in applications
        if query in application["company_name"].casefold()
        and (
            status_filter == "All statuses"
            or (application["status"] or "Unspecified") == status_filter
        )
    ]


def applications_to_csv(applications):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=APPLICATION_COLUMNS)
    writer.writeheader()
    writer.writerows(applications)
    return output.getvalue().encode("utf-8-sig")


def main():
    st.title("Placement Application Tracker")
    initialize_database()
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        flash_message = st.session_state.pop("flash_message", None)
        if flash_message:
            st.success(flash_message)

        with st.form("add_application_form"):
            company_name = st.text_input("Company Name")
            job_role = st.text_input("Job Role")
            application_date = st.date_input("Application Date")
            status = st.selectbox("Status", STATUSES)
            has_interview = st.checkbox("Add an interview date")
            interview_date = (
                st.date_input("Interview Date", min_value=date.today())
                if has_interview
                else None
            )
            submitted = st.form_submit_button("Add Application")

        if submitted:
            if not company_name.strip() or not job_role.strip():
                st.error("Company Name and Job Role cannot be empty.")
            else:
                connection.execute(
                    """
                    INSERT INTO applications
                        (company_name, job_role, application_date, status, interview_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        company_name.strip(),
                        job_role.strip(),
                        application_date.isoformat(),
                        status,
                        interview_date.isoformat() if interview_date else None,
                    ),
                )
                connection.commit()
                st.success("Application added successfully.")

        rows = connection.execute(
            """
            SELECT application_id, company_name, job_role,
                   application_date, status, interview_date
            FROM applications
            ORDER BY application_id
            """
        ).fetchall()
        applications = [
            dict(zip(APPLICATION_COLUMNS, row))
            for row in rows
        ]

        stored_statuses = {
            application["status"] or "Unspecified"
            for application in applications
        }
        additional_statuses = sorted(stored_statuses.difference(STATUSES))
        selectable_statuses = STATUSES + additional_statuses
        status_filter_options = ["All statuses"] + selectable_statuses

        st.header("Applications")
        search_column, filter_column = st.columns(2)
        with search_column:
            company_query = st.text_input("Search by company name")
        with filter_column:
            status_filter = st.selectbox("Filter by status", status_filter_options)

        visible_applications = filter_applications(
            applications, company_query, status_filter
        )
        if visible_applications:
            st.dataframe(
                visible_applications,
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No applications match these search and filter options.")

        export_filtered_column, export_all_column = st.columns(2)
        with export_filtered_column:
            st.download_button(
                "Download filtered results as CSV",
                data=applications_to_csv(visible_applications),
                file_name="filtered_placement_applications.csv",
                mime="text/csv",
            )
        with export_all_column:
            st.download_button(
                "Download all applications as CSV",
                data=applications_to_csv(applications),
                file_name="placement_applications.csv",
                mime="text/csv",
            )

        pending_delete_id = st.session_state.get("pending_delete_id")
        if pending_delete_id is not None:
            pending_application = next(
                (
                    application
                    for application in applications
                    if application["application_id"] == pending_delete_id
                ),
                None,
            )
            if pending_application is None:
                st.session_state.pop("pending_delete_id", None)
            else:
                st.warning(
                    "Delete "
                    f"{pending_application['company_name']} — "
                    f"{pending_application['job_role']}? This cannot be undone."
                )
                confirm_column, cancel_column = st.columns(2)
                with confirm_column:
                    confirm_delete = st.button(
                        "Confirm deletion", key="confirm_delete"
                    )
                with cancel_column:
                    cancel_delete = st.button("Cancel", key="cancel_delete")

                if confirm_delete:
                    connection.execute(
                        "DELETE FROM applications WHERE application_id = ?",
                        (pending_delete_id,),
                    )
                    connection.commit()
                    st.session_state.pop("pending_delete_id", None)
                    st.session_state["flash_message"] = "Application deleted."
                    st.rerun()
                if cancel_delete:
                    st.session_state.pop("pending_delete_id", None)
                    st.rerun()

        st.subheader("Manage applications")
        for application in visible_applications:
            application_id = application["application_id"]
            with st.container(border=True):
                st.markdown(
                    f"**{application['company_name']}** — "
                    f"{application['job_role']}"
                )
                with st.form(f"update_status_{application_id}"):
                    current_status = application["status"] or "Unspecified"
                    selected_status = st.selectbox(
                        "Status",
                        selectable_statuses,
                        index=selectable_statuses.index(current_status),
                        key=f"status_{application_id}",
                    )
                    current_interview_date = application["interview_date"]
                    has_interview = st.checkbox(
                        "Interview date scheduled",
                        value=current_interview_date is not None,
                        key=f"has_interview_{application_id}",
                    )
                    interview_date = (
                        st.date_input(
                            "Interview Date",
                            value=(
                                date.fromisoformat(current_interview_date)
                                if current_interview_date
                                else date.today()
                            ),
                            key=f"interview_date_{application_id}",
                        )
                        if has_interview
                        else None
                    )
                    save_application = st.form_submit_button("Save changes")

                if save_application:
                    connection.execute(
                        """
                        UPDATE applications
                        SET status = ?, interview_date = ?
                        WHERE application_id = ?
                        """,
                        (
                            selected_status,
                            interview_date.isoformat() if interview_date else None,
                            application_id,
                        ),
                    )
                    connection.commit()
                    st.session_state["flash_message"] = "Application changes saved."
                    st.rerun()

                if st.button("Delete application", key=f"delete_{application_id}"):
                    st.session_state["pending_delete_id"] = application_id
                    st.rerun()

        st.metric("Total Applications", len(applications))

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

        rows_by_status = connection.execute(
            """
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            """
        ).fetchall()
        status_counts = {status_name: 0 for status_name in STATUSES}

        for status_name, count in rows_by_status:
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

        upcoming_interviews = connection.execute(
            """
            SELECT company_name, job_role, interview_date, status
            FROM applications
            WHERE interview_date >= ?
            ORDER BY interview_date, company_name COLLATE NOCASE
            """,
            (date.today().isoformat(),),
        ).fetchall()
        st.header("Upcoming Interviews")
        if upcoming_interviews:
            st.dataframe(
                [
                    {
                        "company_name": row[0],
                        "job_role": row[1],
                        "interview_date": row[2],
                        "status": row[3],
                    }
                    for row in upcoming_interviews
                ],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No upcoming interviews have been scheduled.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
