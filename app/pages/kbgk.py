import streamlit as st
from pages.agents import KbgkAgent
from typing import List
import uuid
from textwrap import dedent
from agno.agent import Message


class EchoAgent:
    def respond(self, user_message):
        # Echo the user input as the agent's response
        return user_message


# Streamlit chat UI
st.title("Knowledge Base Gate Keeper")


if "kbgk_session_id" not in st.session_state:
    st.session_state["kbgk_session_id"] = str(uuid.uuid4())

# Display session ID
if "kbgk_session_id" in st.session_state:
    st.markdown("**Session ID:**")
    st.code(st.session_state['kbgk_session_id'], language="text")

if "kbgk_agent" not in st.session_state:
    st.session_state["kbgk_agent"] = KbgkAgent(session_id=st.session_state["kbgk_session_id"])

# Load messages from storage on first run
if "kbgk_messages" not in st.session_state:
    messages: List[Message] = st.session_state["kbgk_agent"].agent.get_messages_for_session()
    st.session_state["kbgk_messages"] = [{"sender": m.role, "message": m.content} for m in messages]

    # Add initial assistant message if no previous messages exist
    if not st.session_state["kbgk_messages"]:
        initial_message = dedent(
            """
سلام! من دستیار مدیریت دانش‌پایه یکتانت هستم.

من به شما کمک می‌کنم تا اسناد جدیدی برای دانش‌پایه ایجاد کنید. 
این اسناد می‌توانند شامل:
• مطالعات موردی (Case Studies)
• راهنماهای کمک (Help Guides) 
• نمونه‌های کمپین‌های موفق
• بهترین شیوه‌های تبلیغاتی

لطفاً بفرمایید چه نوع سندی می‌خواهید ایجاد کنید؟
"""
        )
        st.session_state["kbgk_messages"] = [{"sender": "Assistant", "message": initial_message}]

# Display chat history using chat bubbles
for row in st.session_state["kbgk_messages"]:
    with st.chat_message(row["sender"]):
        message = row["message"]
        if message is None:
            message = ""
        # Detect Persian (RTL) text
        is_rtl = any(
            "\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F" or "\u08A0" <= c <= "\u08FF" for c in message
        )
        if is_rtl:
            rtl_html = f'<div style="text-align: right; direction: rtl;">{message}</div>'
            st.markdown(rtl_html, unsafe_allow_html=True)
        else:
            st.markdown(message)

# Use st.chat_input for user input
user_input = st.chat_input("Type your message...")
if user_input:
    user_msg = {"sender": "user", "message": user_input}
    st.session_state["kbgk_messages"].append(user_msg)
    agent_response = st.session_state["kbgk_agent"].respond(user_input)
    agent_msg = {"sender": "Assistant", "message": agent_response}
    st.session_state["kbgk_messages"].append(agent_msg)
    st.rerun()

# Session management in sidebar
st.sidebar.markdown("### Session Management")

# Input for session ID
new_session_id = st.sidebar.text_input(
    "Enter Session ID to resume:",
    value=st.session_state['kbgk_session_id'], 
    key="kbgk_session_input", 
    label_visibility="collapsed"
)

# Resume session button
if st.sidebar.button("Resume Session", type="secondary"):
    if new_session_id:
        st.session_state["kbgk_session_id"] = new_session_id
        st.session_state["kbgk_agent"] = KbgkAgent(session_id=new_session_id)
        from pages.agents import SqliteStorage
        s: SqliteStorage = st.session_state["kbgk_agent"].agent.storage
        # Load messages for the new session
        messages: List[Message] = st.session_state["kbgk_agent"].agent.get_messages_for_session(new_session_id)
        st.session_state["kbgk_messages"] = []
        for m in messages:
            if m.role == "user":
                st.session_state["kbgk_messages"].append({"sender": m.role, "message": m.content[0]['text']})   
            elif m.role == "assistant":
                st.session_state["kbgk_messages"].append({"sender": m.role, "message": m.content})
        st.rerun()
    else:
        st.sidebar.error("Please enter a session ID")

st.sidebar.markdown("---")

if st.sidebar.button("Clear Chat History", type="primary"):
    st.session_state["kbgk_messages"] = []
    st.rerun() 