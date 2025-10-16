# alert_system.py
import smtplib
from email.message import EmailMessage
import streamlit as st

def gmail_alert_sidebar():
    st.sidebar.subheader("🚨 Send Gmail Alert")
    to_email = st.sidebar.text_input("Recipient Email", key="alert_to")
    subject = st.sidebar.text_input("Subject", key="alert_subject")
    message = st.sidebar.text_area("Message", key="alert_message")

    if st.sidebar.button("🚀 Send Alert", key="alert_button"):
        if to_email and subject and message:
            sender_email = "techscam377@gmail.com"
            app_password = "nksf cbdp nzvr yomp"  # App Password

            msg = EmailMessage()
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(message, subtype="plain")

            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, app_password)
                    server.send_message(msg)
                st.sidebar.success("✅ Alert sent successfully!")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to send alert: {str(e)}")
        else:
            st.sidebar.warning("⚠️ Please fill in all fields before sending.")

