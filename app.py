import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import uuid
from datetime import datetime

# Database Setup
DB_FILE = "business_management.db"


def initialize_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Define tables
    tables = {
        "Leads": """
            CREATE TABLE IF NOT EXISTS Leads (
                LeadID TEXT PRIMARY KEY,
                LeadSource TEXT,
                ReferralSource TEXT,
                LeadCost REAL,
                ReceivedDate TEXT,
                Status TEXT
            )
        """,
        "Projects": """
            CREATE TABLE IF NOT EXISTS Projects (
                ProjectID TEXT PRIMARY KEY,
                LeadID TEXT,
                ProjectType TEXT,
                StartDate TEXT,
                ContractValue REAL,
                FOREIGN KEY (LeadID) REFERENCES Leads(LeadID)
            )
        """,
        "DailyUpdates": """
            CREATE TABLE IF NOT EXISTS DailyUpdates (
                UpdateID TEXT PRIMARY KEY,
                ProjectID TEXT,
                Date TEXT,
                HoursWorked REAL,
                MaterialCosts REAL,
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
            )
        """,
        "Equipment": """
            CREATE TABLE IF NOT EXISTS Equipment (
                EquipmentID TEXT PRIMARY KEY,
                Type TEXT,
                PurchaseDate TEXT,
                CurrentStatus TEXT
            )
        """,
        "Vendors": """
            CREATE TABLE IF NOT EXISTS Vendors (
                VendorID TEXT PRIMARY KEY,
                Name TEXT,
                ServiceType TEXT,
                RateStructure TEXT
            )
        """
    }

    # Execute table creation
    for table_name, create_stmt in tables.items():
        cursor.execute(create_stmt)

    conn.commit()
    conn.close()


def execute_query(query, params=None, fetch=False):
    """Execute a query on the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    if fetch:
        results = cursor.fetchall()
        conn.close()
        return results

    conn.commit()
    conn.close()


def insert_row(table, data):
    """Insert a row into a table."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    execute_query(query, list(data.values()))


def fetch_table_data(table):
    """Fetch all rows from a table."""
    query = f"SELECT * FROM {table}"
    return pd.DataFrame(execute_query(query, fetch=True), columns=[desc[0] for desc in sqlite3.connect(DB_FILE).cursor().execute(query).description])


def generate_unique_id():
    """Generate a unique identifier."""
    return str(uuid.uuid4())[:8]


# Dashboard
def dashboard():
    st.title("Business Management Dashboard")

    # Load data
    projects_df = fetch_table_data("Projects")
    if not projects_df.empty:
        st.subheader("Project Profitability Heatmap")
        fig = px.density_heatmap(
            projects_df,
            x="ProjectType",
            y="ContractValue",
            title="Profitability by Project Type"
        )
        st.plotly_chart(fig)

        st.subheader("Cash Flow Forecast")
        projects_df["Month"] = pd.to_datetime(projects_df["StartDate"]).dt.to_period("M")
        cash_flow = projects_df.groupby("Month")["ContractValue"].sum().reset_index()
        fig = px.line(
            cash_flow,
            x="Month",
            y="ContractValue",
            title="Monthly Contract Value"
        )
        st.plotly_chart(fig)
    else:
        st.info("No projects data available. Please add projects.")


# Input Forms
def input_forms():
    st.title("Data Input Forms")

    tabs = st.tabs(["Leads", "Projects", "Daily Updates", "Equipment", "Vendors"])

    # Leads Form
    with tabs[0]:
        st.header("Leads Form")
        lead_data = {
            "LeadID": generate_unique_id(),
            "LeadSource": st.text_input("Lead Source"),
            "ReferralSource": st.text_input("Referral Source"),
            "LeadCost": st.number_input("Lead Cost", min_value=0.0),
            "ReceivedDate": st.date_input("Received Date").strftime("%Y-%m-%d"),
            "Status": st.selectbox("Status", ["New", "Contacted", "Converted"])
        }

        if st.button("Save Lead"):
            insert_row("Leads", lead_data)
            st.success("Lead saved successfully!")

    # Projects Form
    with tabs[1]:
        st.header("Projects Form")
        leads_df = fetch_table_data("Leads")
        lead_ids = leads_df["LeadID"].tolist() if not leads_df.empty else ["No Leads Available"]

        project_data = {
            "ProjectID": generate_unique_id(),
            "LeadID": st.selectbox("Lead ID", lead_ids),
            "ProjectType": st.text_input("Project Type"),
            "StartDate": st.date_input("Start Date").strftime("%Y-%m-%d"),
            "ContractValue": st.number_input("Contract Value", min_value=0.0)
        }

        if st.button("Save Project"):
            if project_data["LeadID"] == "No Leads Available":
                st.error("Please add a lead before creating a project.")
            else:
                insert_row("Projects", project_data)
                st.success("Project saved successfully!")

    # Other Forms
    # Similar logic for "Daily Updates," "Equipment," and "Vendors."


# Data Management
def data_management():
    st.title("Data Management")
    tables = ["Leads", "Projects", "DailyUpdates", "Equipment", "Vendors"]

    for table in tables:
        st.header(f"{table} Data")
        df = fetch_table_data(table)

        if not df.empty:
            st.dataframe(df)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Export {table} to CSV"):
                    df.to_csv(f"{table.lower()}_data.csv", index=False)
                    st.success(f"{table} data exported successfully!")
            with col2:
                if st.button(f"Clear {table} Data"):
                    execute_query(f"DELETE FROM {table}")
                    st.warning(f"All data in {table} cleared.")
        else:
            st.info(f"No data available in {table}.")


# Main Function
def main():
    st.set_page_config(layout="wide", page_title="Business Management App")
    initialize_db()

    menu = st.sidebar.radio("Navigation", ["Dashboard", "Input Forms", "Data Management"])

    if menu == "Dashboard":
        dashboard()
    elif menu == "Input Forms":
        input_forms()
    elif menu == "Data Management":
        data_management()


if __name__ == "__main__":
    main()
