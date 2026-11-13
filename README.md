# Placement Application Tracker

A Streamlit app for tracking job applications by company, role, application
date, and status.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create the local SQLite database:

   ```powershell
   python init_db.py
   ```

4. Start the app:

   ```powershell
   streamlit run app.py
   ```

Application records are stored in the local `placements.db` file. That file is
ignored by Git so personal application data is not published.