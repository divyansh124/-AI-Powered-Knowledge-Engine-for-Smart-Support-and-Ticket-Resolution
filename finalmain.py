import streamlit as st
from dashboard2 import dashboard
from chatbot import chatbot
from alert import gmail_alert_sidebar  # your alert function

# -----------------------------
# Session state to remember page
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "AI ticket assistant"

st.sidebar.header("AI Ticket Helping System")

# -----------------------------
# Navigation buttons
# -----------------------------
if st.sidebar.button("💬 AI Ticket Assistant"):
    st.session_state.page = "AI ticket assistant"

if st.sidebar.button("📊 Analytic Dashboard"):
    st.session_state.page = "Analytic Dashboard"

# -----------------------------
# Separation line
# -----------------------------
st.sidebar.markdown("---")

# -----------------------------
# Gmail alert in sidebar (only on Dashboard)
# -----------------------------
if st.session_state.page == "Analytic Dashboard":
    gmail_alert_sidebar()

# -----------------------------
# Render selected page
# -----------------------------
if st.session_state.page == "AI ticket assistant":
    chatbot()
elif st.session_state.page == "Analytic Dashboard":
    dashboard()
