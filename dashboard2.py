import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter
def dashboard():
  
    # -----------------------------
    # Google Sheets setup
    # -----------------------------
    scope = ["https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gspread_client = gspread.authorize(creds)

    SHEET_NAME = "MyDatabaseSheet"
    sheet = gspread_client.open(SHEET_NAME)
    ticket_sheet = sheet.sheet1

    # -----------------------------
    # Load data
    # -----------------------------
    all_tickets = ticket_sheet.get_all_records()
    df = pd.DataFrame(all_tickets)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    if df.empty:
        st.warning("No ticket data available yet!")
        st.stop()

    # Pending subset
    pending_data = df[df['ticket_status'].str.lower() == 'pending']
    st.title("📊 Ticket Analytics Dashboard")

    # -----------------------------
    # KPIs
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)

    total_tickets = len(df)
    resolved = df[df["ticket_status"].str.lower() == "closed"].shape[0]
    unresolved = df[df["ticket_status"].str.lower() == "pending"].shape[0]
    resolution_per = (resolved / total_tickets) * 100 if total_tickets > 0 else 0

    col1.metric("Total Tickets", total_tickets)
    col2.metric("Resolved", resolved)
    col3.metric("Unresolved", unresolved)
    col4.metric("Resolution Percentage", f"{resolution_per:.2f}%")

    # -----------------------------
    # Donut charts
    # -----------------------------
    col4, col5 = st.columns(2)

    # Ticket status distribution
    if "ticket_status" in df.columns:
        status_counts = df["ticket_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_status = px.pie(
            status_counts,
            values="Count",
            names="Status",
            hole=0.4,
            title="Ticket Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        col4.plotly_chart(fig_status, use_container_width=True)

    # Ticket category distribution
    if "ticket_category" in df.columns:
        category_counts = df["ticket_category"].value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]
        fig_category = px.pie(
            category_counts,
            values="Count",
            names="Category",
            hole=0.4,
            title="Ticket Category Distribution",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        col5.plotly_chart(fig_category, use_container_width=True)

    # -----------------------------
    # Pending query distribution
    # -----------------------------
    col6, = st.columns(1)

    if not pending_data.empty and "ticket_category" in pending_data.columns:
        pending_counts = pending_data["ticket_category"].value_counts().reset_index()
        pending_counts.columns = ["Category", "Count"]
        fig_pending = px.pie(
            pending_counts,
            values="Count",
            names="Category",
            hole=0.4,
            title="Pending Query Distribution",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        col6.plotly_chart(fig_pending, use_container_width=True)

    # -----------------------------
    # Track article references / usage
    # -----------------------------
    st.subheader("📌 Article / Knowledge Base Insights")

    if "ticket_content" in df.columns:
        # Count frequency of each unique content/article
        article_counts = Counter(df["ticket_content"])
        article_df = pd.DataFrame(article_counts.items(), columns=["Article", "References"])
        article_df = article_df.sort_values(by="References", ascending=False)

        st.markdown("**Top Referenced Articles / Queries**")
        st.dataframe(article_df.head(10), use_container_width=True)

        # Identify articles never referenced (if you have a list of all articles)
        # Example: `all_articles = ["Article1", "Article2", ...]`
        # unused_articles = list(set(all_articles) - set(article_df["Article"]))
        # st.markdown("**Unused Articles / Gaps**")
        # st.write(unused_articles)

    # -----------------------------
    # Alerts for low-coverage categories
    # -----------------------------
    st.subheader("🚨 Low Coverage Categories / Alerts")

    if "ticket_category" in df.columns:
        category_counts_dict = df["ticket_category"].value_counts().to_dict()
        # Define threshold (e.g., categories with <5 tickets)
        threshold = 5
        low_coverage = {cat: count for cat, count in category_counts_dict.items() if count < threshold}

        if low_coverage:
            st.warning(f"Categories with very few tickets (<{threshold}): {low_coverage}")
        else:
            st.success("All categories have sufficient coverage!")

    # -----------------------------
    # Tabs for ticket tables
    # -----------------------------
    st.subheader("📋 Ticket Tables")
    tab1, tab2 = st.tabs(["🚨 Unresolved Queries", "📑 All Queries"])

    with tab1:
        unresolved_df = df[df["ticket_status"].str.lower() == "pending"]
        if not unresolved_df.empty:
            st.dataframe(unresolved_df, use_container_width=True)
        else:
            st.success("🎉 No unresolved queries!")

    with tab2:
        st.dataframe(df, use_container_width=True)
