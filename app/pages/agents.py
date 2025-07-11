from __future__ import annotations

import os
import uuid
from textwrap import dedent
from typing import Optional

from agno.agent import Agent, Message
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from datetime import datetime

from pages.models import CampaignRequest, CampaignRequestDB, CampaignPlan, Task
from pages.kb import campaign_planner_retriever, get_documents_for_user_request
from pages.crud import (
    insert_campaign_request,
    fetch_latest_campaign_request,
    insert_campaign_plan,
)
from pages.config import (
    OPENAI_BASE_URL,
    get_openai_api_key,
    GPT_MODEL_ID,
    FIRST_AGENT_DB_PATH,
    CAMPAIGN_PLANNER_DB_PATH,
    FIRST_AGENT_TABLE_NAME,
    CAMPAIGN_PLANNER_TABLE_NAME,
    AGENT_DEBUG_MODE,
    get_tasks_dir_path,
)


def persist_user_request(user_request: CampaignRequest, agent: Optional[Agent] = None, **kwargs) -> None:
    """Store the request for this session via the CRUD helpers."""
    user_request = CampaignRequestDB(
        **user_request.model_dump(),
        session_id=agent.session_id,
        advertiser_id=agent.user_id,
        created_at=datetime.now(),
        status="new"
        )
    insert_campaign_request(user_request)


class FirstAgent:
    """Collects all details needed to build a CampaignRequest."""

    def __init__(self, session_id: str, user_id: str = "1"):
        self.agent = Agent(
            name="Greetings Agent",
            model=OpenAIChat(
                id=GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[persist_user_request],
            # TODO: Change the instruction to english.
            instructions=[
                dedent(
                    f""" 
                          تو یک دستیار هوشمند در یکتانت هستی و اسم تو جن‌کمپین است.
                          هدف تو راهنمایی و کسب اطلاعات لازم از مشتریان یکتانت در جهت ساخت کمپین‌های تبلیغاتی است
                          ابتدا باید با پرسیدن سوالات مناسب، اطلاعات لازم برای ساخت کمپین رو به دست بیاری
                          بعد از اینکه سوالات لازم رو از کاربر پرسیدی و اطلاعات کافی به دست آوردی باید با استفاده از ابزار 
                          persist_user_request
                          یک کلاس 
                          CampaignRequest 
                          بسازی.
                          """
                )
            ],
            storage=SqliteStorage(table_name=FIRST_AGENT_TABLE_NAME, db_file=FIRST_AGENT_DB_PATH),
            add_datetime_to_instructions=True,
            # Adds the history of the conversation to the messages
            add_history_to_messages=True,
            # Number of history responses to add to the messages
            num_history_responses=5,
            # Adds markdown formatting to the messages
            markdown=True,
            user_id=user_id,
            session_id=session_id,
            debug_mode=AGENT_DEBUG_MODE,
            telemetry=False,
            monitoring=False,
        )
        self.agent.initialize_agent()
        self.agent.read_from_storage(session_id=session_id)

    def respond(self, user_message: str):
        reply = self.agent.run(Message(role="user", content=[{"type": "text", "text": user_message}]))
        return reply.content


class CampaignPlanner:
    """Takes the saved CampaignRequest and drafts a CampaignPlan."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agent = Agent(
            name="Campaign Planner Agent",
            model=OpenAIChat(
                id=GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[],
            goal="Create a CampaignPlan to handle the given UserRequest in persian",
            instructions=[dedent("""
                          You're given a UserRequest to create a digital marketing campaign in Yektanet. 
                          Also, previous campaign plans and details related to similar businesses are provided. 

                          * CampaignPlan.needs_confirmation should be True, If provided samples are not similar enough.  
                          * Search the knowledge_base using given UserRequest in persian, include business type and goal.
                          * Only call the search_knowledge tool once in each response.    

                          Also, related documents names and types are provided to make you aware of the available
                                  documents in the knowledge base.
                          """)],
            storage=SqliteStorage(table_name=CAMPAIGN_PLANNER_TABLE_NAME, db_file=CAMPAIGN_PLANNER_DB_PATH),

            add_datetime_to_instructions=True,
            # Adds the history of the conversation to the messages
            add_history_to_messages=True,
            # Number of history responses to add to the messages
            num_history_responses=5,
            # Adds markdown formatting to the messages
            markdown=True,
            session_id=session_id,
            debug_mode=AGENT_DEBUG_MODE,
            response_model=CampaignPlan,
            retriever=campaign_planner_retriever,
            search_knowledge=True,
        )

    def respond(self) -> CampaignPlan:
        campaign_request = fetch_latest_campaign_request(self.session_id)

        if campaign_request is None:
            raise RuntimeError("No CampaignRequest stored for this session yet.")

        # Get relevant documents for the user request
        documents_info = get_documents_for_user_request(campaign_request)

        # Combine user request with documents info
        combined_input = f"CampaignRequest:\n{campaign_request.model_dump_json()}\n"
        combined_input += f"Related documents:\n{documents_info}"

        reply = self.agent.run(combined_input)
        campaign_plan: CampaignPlan = reply.content

        insert_campaign_plan(self.session_id, campaign_plan)

        task = Task(type="confirm_campaign_plan", description="Confirm the campaign plan or edit it if needed", 
                    status="pending", session_id=self.agent.session_id)
        with open(f"{get_tasks_dir_path()}/{uuid.uuid4()}.json", "w") as f:
            f.write(task.model_dump_json())

        return campaign_plan
