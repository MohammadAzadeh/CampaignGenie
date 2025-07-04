import os
from agno.agent import Agent, Message
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from textwrap import dedent

from pages.models import CampaignRequest, CampaignPlan
from pages.kb import campaign_planner_retriever

# TODO: Move all Storage Config to a file
agent_storage: str = "pages/files/tmp/agents.db"


def save_user_request(agent: Agent, user_request: CampaignRequest):
    """
    Use this function to save user request.

    Args:
        user_request (UserRequest): detailed user request
    """
    SESSION_ID = agent.session_id
    with open(f"pages/files/user_requests/{SESSION_ID}.json", "w") as f:
        f.write(user_request.model_dump_json())


class FirstAgent:
    def __init__(self, session_id):
        self.agent = Agent(
            name="Greetings Agent",
            model=OpenAIChat(
                id="gpt-4.1-mini", base_url="https://api.metisai.ir/openai/v1", api_key=os.environ["METIS_API_KEY"]
            ),
            tools=[save_user_request],
            # TODO: Change the instruction to english.
            instructions=[
                dedent(
                    f""" 
                          تو یک دستیار هوشمند در یکتانت هستی و اسم تو جن‌کمپین است.
                          هدف تو راهنمایی و کسب اطلاعات لازم از مشتریان یکتانت در جهت ساخت کمپین‌های تبلیغاتی است
                          ابتدا باید با پرسیدن سوالات مناسب، اطلاعات لازم برای ساخت کمپین رو به دست بیاری
                          بعد از اینکه سوالات لازم رو از کاربر پرسیدی و اطلاعات کافی به دست آوردی باید با استفاده از ابزار 
                          save_user_request
                          یک کلاس 
                          UserRequest 
                          بسازی.
                          """
                )
            ],
            # Store the agent sessions in a sqlite database
            storage=SqliteStorage(table_name="first_agent", db_file=agent_storage),
            # Adds the current date and time to the instructions
            add_datetime_to_instructions=True,
            # Adds the history of the conversation to the messages
            add_history_to_messages=True,
            # Number of history responses to add to the messages
            num_history_responses=5,
            # Adds markdown formatting to the messages
            markdown=True,
            session_id=session_id,
            debug_mode=True,
        )

    def respond(self, user_message):
        msg = Message(
            role="user",
            content=[
                {"type": "text", "text": user_message},
                # TODO: Add support for image content
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         "url": "path/to/image",
                #     },
                # },
            ],
        )
        return self.agent.run(msg).content


class CampaignPlanner:
    def __init__(self, session_id):
        self.agent = Agent(
            name="Campaign Planner Agent",
            model=OpenAIChat(
                id="gpt-4.1-mini", base_url="https://api.metisai.ir/openai/v1", api_key=os.environ["METIS_API_KEY"]
            ),
            tools=[],
            goal="Create a CampaignPlan to handle the given UserRequest in persian",
            instructions=[
                dedent(
                    f"""
                          You're given a CampaignRequest to create a digital marketing campaign in Yektanet. 
                          Also, previous campaign plans and details related to similar businesses are provided. 

                          * CampaignPlan.needs_confirmation should be True, If provided samples are not similar enough.  
                          * Search the knowledge_base using given UserRequest in persian.             
                          """
                )
            ],
            # Store the agent sessions in a sqlite database
            # storage=SqliteStorage(table_name="second_agent", db_file=agent_storage),
            # Adds the current date and time to the instructions
            add_datetime_to_instructions=True,
            # Adds the history of the conversation to the messages
            add_history_to_messages=True,
            # Number of history responses to add to the messages
            num_history_responses=5,
            # Adds markdown formatting to the messages
            markdown=True,
            session_id=session_id,
            debug_mode=True,
            response_model=CampaignPlan,
            retriever=campaign_planner_retriever,
            search_knowledge=True,
        )

    def respond(self):
        with open(f"pages/files/user_requests/{self.agent.session_id}.json", "r") as f:
            a = f.read()
        resp = self.agent.run(a)
        with open(f"pages/files/campaign_plans/{self.agent.session_id}.json", "w") as f:
            f.write(resp.content.model_dump_json())
