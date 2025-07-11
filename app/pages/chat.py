import streamlit as st
from pages.agents import FirstAgent
from typing import List
import uuid
from textwrap import dedent
from agno.agent import Message


class EchoAgent:
    def respond(self, user_message):
        # Echo the user input as the agent's response
        return user_message


# Streamlit chat UI
st.title("Chat with Agent")


if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Display session ID
if "session_id" in st.session_state:
    st.markdown("**Session ID:**")
    st.code(st.session_state['session_id'], language="text")

if "agent" not in st.session_state:
    st.session_state["agent"] = FirstAgent(session_id=st.session_state["session_id"])

# Load messages from TinyDB on first run
if "messages" not in st.session_state:
    messages: List[Message] = st.session_state["agent"].agent.get_messages_for_session()
    st.session_state["messages"] = [{"sender": m.role, "message": m.content} for m in messages]

    # Add initial assistant message if no previous messages exist
    if not st.session_state["messages"]:
        initial_message = dedent(
            """
سلام! من جن‌کمپین هستم، دستیار هوشمند یکتانت برای ساخت کمپین‌های تبلیغاتی.


من به شما کمک میکنم که اطلاعات لازم برای ساخت کمپین‌های تلبیغاتی رو مشخص کنیم
 و در نهایت یک درخواست ساخت کمپین برای شما ثبت میکنم
   تا همکاران ما در سریع‌ترین زمان کمپین شما را بسازند.

لطفاً بفرمایید قصد دارید برای چه کسب‌وکاری تبلیغات داشته باشید؟
"""
        )
        st.session_state["messages"] = [{"sender": "Assistant", "message": initial_message}]

# Display chat history using chat bubbles
for row in st.session_state["messages"]:
    with st.chat_message(row["sender"]):
        message = row["message"]
        if message is None:
            message = ""        # Detect Persian (RTL) text
        is_rtl = any(
            "\u0600" <= c <= "\u06FF" or "\u0750" <= c <= "\u077F" or "\u08A0" <= c <= "\u08FF" for c in message
        )
        if is_rtl:
            rtl_html = f'<div style="text-align: right; direction: rtl;">' f"{message}</div>"
            st.markdown(rtl_html, unsafe_allow_html=True)
        else:
            st.markdown(message)

# Use st.chat_input for user input
user_input = st.chat_input("Type your message...")
if user_input:
    user_msg = {"sender": "user", "message": user_input}
    st.session_state["messages"].append(user_msg)
    agent_response = st.session_state["agent"].respond(user_input)
    agent_msg = {"sender": "Assistant", "message": agent_response}
    st.session_state["messages"].append(agent_msg)
    st.rerun()

# Session management in sidebar
st.sidebar.markdown("### Session Management")

# Input for session ID
# new_session_id = st.sidebar.text_input("Enter Session ID to resume:", key="session_input")
new_session_id = st.sidebar.text_input(
    "Enter Session ID to resume:",  # Descriptive label for accessibility
    value=st.session_state['session_id'], 
    key="session_input", 
    label_visibility="collapsed"  # This hides the label visually
)
# Resume session button
if st.sidebar.button("Resume Session", type="secondary"):
    if new_session_id:
        st.session_state["session_id"] = new_session_id
        st.session_state["agent"] = FirstAgent(session_id=new_session_id)
        from pages.agents import SqliteStorage
        s: SqliteStorage = st.session_state["agent"].agent.storage
        # Load messages for the new session
        messages: List[Message] = st.session_state["agent"].agent.get_messages_for_session(new_session_id)
        for m in messages:
            if m.role == "user":
                st.session_state["messages"].append({"sender": m.role, "message": m.content[0]['text']})   
            elif m.role == "assistant":
                st.session_state["messages"].append({"sender": m.role, "message": m.content})
        st.rerun()
    else:
        st.sidebar.error("Please enter a session ID")

st.sidebar.markdown("---")

if st.sidebar.button("Clear Chat History", type="primary"):
    st.session_state["messages"] = []
    st.rerun()
