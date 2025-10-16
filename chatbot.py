import streamlit as st
from ai3 import agent  # Import your LangChain agent with memory
def chatbot():
    st.set_page_config(page_title="AI Ticket Assistant Chatbot", layout="wide")
    st.title("🤖 AI Ticket Assistant Chatbot")

    st.markdown(
        "Chat with the AI assistant about tickets, lookup, update, or save tickets."
    )

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat input
    user_input = st.text_input("Type your message here and press Enter:", key="input")

    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get AI response
        with st.spinner("🤖 AI is typing..."):
            response = agent.invoke({"input": user_input})
            ai_message = response.get("output", "No response from agent.")

        # Add AI message to chat
        st.session_state.messages.append({"role": "assistant", "content": ai_message})

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI:** {message['content']}")
