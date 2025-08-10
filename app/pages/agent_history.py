import streamlit as st
from typing import List, Dict
import json
from agno.storage.sqlite import SqliteStorage

from pages.agents import FirstAgent, CampaignPlanner, KbgkAgent, CrawlerAgent
from pages.config import (
    FIRST_AGENT_DB_PATH,
    CAMPAIGN_PLANNER_DB_PATH,
    KBGK_AGENT_DB_PATH,
    CRAWLER_AGENT_DB_PATH,
    FIRST_AGENT_TABLE_NAME,
    CAMPAIGN_PLANNER_TABLE_NAME,
    KBGK_AGENT_TABLE_NAME,
    CRAWLER_AGENT_TABLE_NAME,
)


def get_session_messages(agent, session_id: str) -> List[Dict]:
    """Get all messages for a specific session from the storage."""
    try:
        # Get messages for the session using agno API
        messages = agent.agent.get_messages_for_session(session_id)

        formatted_messages = []
        for msg in messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content,
                "created_at": getattr(msg, "created_at", None),
                "tool_calls": getattr(msg, "tool_calls", None),
                "tool_results": getattr(msg, "tool_results", None),
            }
            formatted_messages.append(message_dict)

        return formatted_messages
    except Exception as e:
        st.error(f"Error fetching messages: {str(e)}")
        return []


def format_tool_calls(tool_calls: List[Dict]) -> str:
    """Format tool calls for display."""
    if not tool_calls:
        return ""

    formatted = []
    for i, call in enumerate(tool_calls, 1):
        tool_name = call.get("function", {}).get("name", "Unknown Tool")
        args = call.get("function", {}).get("arguments", {})

        formatted.append(f"**Tool {i}: {tool_name}**")
        if args:
            formatted.append("```json")
            formatted.append(json.dumps(args, indent=2, ensure_ascii=False))
            formatted.append("```")
        formatted.append("")

    return "\n".join(formatted)


def format_tool_results(tool_results: List[Dict]) -> str:
    """Format tool results for display."""
    if not tool_results:
        return ""

    formatted = []
    for i, result in enumerate(tool_results, 1):
        tool_name = result.get("name", "Unknown Tool")
        content = result.get("content", "")

        formatted.append(f"**Result {i}: {tool_name}**")
        if content:
            formatted.append("```")
            formatted.append(str(content))
            formatted.append("```")
        formatted.append("")

    return "\n".join(formatted)


def get_agent_instance(agent_name: str, session_id: str):
    """Get an instance of the appropriate agent class."""
    if agent_name == "First Agent (Greetings)":
        agent = FirstAgent(session_id=session_id)
    elif agent_name == "Campaign Planner":
        agent = CampaignPlanner(session_id=session_id)
    elif agent_name == "Knowledge Base Gate Keeper":
        agent = KbgkAgent(session_id=session_id)
    elif agent_name == "Crawler Agent":
        agent = CrawlerAgent(session_id=session_id)
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent.agent.initialize_agent()
    agent.agent.read_from_storage(session_id=session_id)
    return agent


def display_agent_interaction(agent_name: str, session_id: str):
    """Display an interactive interface for the selected agent."""
    st.markdown("### Agent Interaction")
    st.markdown("You can interact with the agent directly here.")

    try:
        agent_instance = get_agent_instance(agent_name, session_id)

        # Display agent info
        st.info(f"**Agent:** {agent_name}\n**Session:** {session_id}")

        # Input for user message
        user_message = st.text_area(
            "Enter your message:", height=100, placeholder="Type your message here..."
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Send Message", type="primary"):
                if user_message.strip():
                    with st.spinner("Processing..."):
                        try:
                            if hasattr(agent_instance, "respond"):
                                response = agent_instance.respond(user_message)
                                st.success("Response received!")
                                st.markdown("**Agent Response:**")
                                st.markdown(response)
                            else:
                                st.error(
                                    "This agent doesn't support direct interaction."
                                )
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter a message.")

        with col2:
            if st.button("Clear Session"):
                try:
                    agent_instance.agent.storage.delete_session(session_id)
                    st.success("Session cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing session: {str(e)}")

    except Exception as e:
        st.error(f"Error creating agent instance: {str(e)}")


def main():
    st.title("Agent Message History Viewer")
    st.markdown("View message history for any agent and session")

    # Agent selection
    st.sidebar.markdown("### Select Agent")

    agents = {
        "First Agent (Greetings)": {
            "db_path": FIRST_AGENT_DB_PATH,
            "table_name": FIRST_AGENT_TABLE_NAME,
        },
        "Campaign Planner": {
            "db_path": CAMPAIGN_PLANNER_DB_PATH,
            "table_name": CAMPAIGN_PLANNER_TABLE_NAME,
        },
        "Knowledge Base Gate Keeper": {
            "db_path": KBGK_AGENT_DB_PATH,
            "table_name": KBGK_AGENT_TABLE_NAME,
        },
        "Crawler Agent": {
            "db_path": CRAWLER_AGENT_DB_PATH,
            "table_name": CRAWLER_AGENT_TABLE_NAME,
        },
    }

    selected_agent = st.sidebar.selectbox("Choose Agent:", list(agents.keys()))

    if selected_agent:
        # Get sessions for selected agent
        try:
            # Create a temporary agent instance to get storage
            temp_agent = get_agent_instance(selected_agent, "temp_session")
        except Exception as e:
            st.error(f"Error accessing agent storage: {str(e)}")
            return
        session_ids = temp_agent.agent.storage.get_all_session_ids()

        if not session_ids:
            st.warning(f"No sessions found for {selected_agent}")
            return

        # Session selection
        st.sidebar.markdown("### Select Session")
        selected_session = st.sidebar.selectbox(
            "Choose Session:",
            session_ids,
            format_func=lambda x: (
                f"Session: {x[:8]}..." if len(x) > 8 else f"Session: {x}"
            ),
        )

        if selected_session:
            # Create tabs for different views
            tab1, tab2 = st.tabs(["📜 Message History", "💬 Agent Interaction"])

            with tab1:
                # Get messages for selected session
                agent_instance = get_agent_instance(selected_agent, selected_session)
                messages = get_session_messages(agent_instance, selected_session)

                if not messages:
                    st.warning(f"No messages found for session {selected_session}")
                else:
                    # Display session info
                    st.markdown(f"### Session: `{selected_session}`")
                    st.markdown(f"**Agent:** {selected_agent}")
                    st.markdown(f"**Total Messages:** {len(messages)}")

                    # Display messages
                    st.markdown("### Message History")

                    for i, message in enumerate(messages, 1):
                        with st.expander(
                            f"Message {i} - {message['role'].title()}", expanded=True
                        ):
                            col1, col2 = st.columns([1, 8])

                            with col1:
                                st.markdown(f"**Role:** {message['role']}")
                                if message["created_at"]:
                                    st.markdown(f"**Time:** {message['created_at']}")

                            with col2:
                                # Display content
                                if message["content"]:
                                    st.markdown("**Content:**")
                                    # Handle Persian text
                                    content_str = str(message["content"])
                                    is_rtl = any(
                                        "\u0600" <= c <= "\u06ff"
                                        or "\u0750" <= c <= "\u077f"
                                        or "\u08a0" <= c <= "\u08ff"
                                        for c in content_str
                                    )
                                    if is_rtl:
                                        st.markdown(
                                            f'<div dir="rtl">{content_str}</div>',
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(content_str)

                                # Display tool calls
                                if message["tool_calls"]:
                                    st.markdown("**Tool Calls:**")
                                    st.markdown(
                                        format_tool_calls(message["tool_calls"])
                                    )

                                # Display tool results
                                if message["tool_results"]:
                                    st.markdown("**Tool Results:**")
                                    st.markdown(
                                        format_tool_results(message["tool_results"])
                                    )

                            st.divider()

                    # Export functionality
                    st.sidebar.markdown("### Export")
                    if st.sidebar.button("Export Session History"):
                        export_data = {
                            "agent": selected_agent,
                            "session_id": selected_session,
                            "messages": messages,
                        }

                        # Create download button
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(export_data, indent=2, ensure_ascii=False),
                            file_name=f"agent_history_{selected_session[:8]}.json",
                            mime="application/json",
                        )

            with tab2:
                # Display agent interaction interface
                display_agent_interaction(selected_agent, selected_session)


if __name__ == "__main__":
    main()
