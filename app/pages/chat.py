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
    print("SessionID", st.session_state["session_id"])

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
        # Detect Persian (RTL) text
        message = row["message"]
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

if st.sidebar.button("Clear Chat History", type="primary"):
    st.session_state["messages"] = []
    st.rerun()
