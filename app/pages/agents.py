from __future__ import annotations

import os
import uuid
from textwrap import dedent
from typing import Optional

from agno.agent import Agent, Message
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from agno.tools.crawl4ai import Crawl4aiTools

from datetime import datetime

from pages.models import CampaignRequest, CampaignRequestDB, CampaignPlan, GenerateCampaignPlanTask, CampaignPlanDB
from pages.kb import campaign_planner_retriever, get_documents_for_user_request, knowledge_base, search_yektanet, add_documents_to_knowledge_base
from pages.prompts import YEKTANET_SERVICES
from pages.config import (
    OPENAI_BASE_URL,
    get_openai_api_key,
    GPT_MODEL_ID,
    MINI_GPT_MODEL_ID,
    FIRST_AGENT_DB_PATH,
    CAMPAIGN_PLANNER_DB_PATH,
    KBGK_AGENT_DB_PATH,
    FIRST_AGENT_TABLE_NAME,
    CAMPAIGN_PLANNER_TABLE_NAME,
    KBGK_AGENT_TABLE_NAME,
    AGENT_DEBUG_MODE,
    get_tasks_dir_path,
    CRAWLER_AGENT_DB_PATH,
    CRAWLER_AGENT_TABLE_NAME,
    )
from pages.mongodb_utils import insert_campaign_request, insert_task, fetch_one_campaign_request, insert_campaign_plan


def persist_campaign_request(campaign_request: CampaignRequest, agent: Optional[Agent] = None, **kwargs) -> None:
    """Store the request for this session via MongoDB."""
    campaign_request_db = CampaignRequestDB(
        **campaign_request.model_dump(),
        campaign_request_id=str(uuid.uuid4()),
        session_id=agent.session_id,
        advertiser_id=agent.user_id,
        created_at=datetime.now(),
        status="new"
    )
    
    insert_campaign_request(campaign_request_db)
    task = GenerateCampaignPlanTask(
        type="generate_campaign_plan",
        description="Generate a Campaign Plan for given CampaignRequest",
        status="new",
        session_id=str(uuid.uuid4()),
        created_at=datetime.now(),
        campaign_request_id=campaign_request_db.campaign_request_id
    )
    insert_task(task)

def ask_from_knowledge_base(
    question: str
) -> str:
    """
    Answers a question using the knowledge base.
    It creates an agent with the knowledge base and asks the question to it.
    
    Args:
        question (str): The question to answer

    Returns:
        str: The answer to the question
    """
    try:
        agent = Agent(
            model=OpenAIChat(
                id=MINI_GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[campaign_planner_retriever],
            instructions=[
                "Always search your knowledge before answering the question.",
                "Only include the output in your response. No other text.",
                "Related documents are provided to give you an idea of the available documents.",
                "In each call num_documents MUST BE ALWAYS 2, instead you can do a few calls to get more information.",
            ],
            markdown=True,
            debug_mode=AGENT_DEBUG_MODE,
            telemetry=False,
            monitoring=False,
        )
        documents = knowledge_base.search(query=question, num_documents=10)
        
        if not documents:
            return "No documents found"
        
        # Generate formatted message with document information
        message_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_dict = doc.to_dict()
            name = doc_dict.get('name', 'نامشخص')
            content_type = doc_dict.get('meta_data', {}).get('contenttype', 'نامشخص')
            
            message_parts.append(f"{i}. {name} ({content_type})")
        
        related_docs = "\n\n".join(message_parts)
    
        response = agent.run(f"Question: {question}\n\n Documents: {related_docs}")
        return response
    except Exception as e:
        print(f"Error during knowledge base search: {str(e)}")
        return f"Error during knowledge base search: {str(e)}"


class FirstAgent:
    """Collects all details needed to build a CampaignRequest."""

    def __init__(self, session_id: str, user_id: str = "1"):
        self.agent = Agent(
            name="Greetings Agent",
            model=OpenAIChat(
                id=MINI_GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[
                persist_campaign_request,
                agentic_crawl_url],
            instructions=[
                dedent(
                    f""" 
                    You are a smart assistant for Yektanet, called CampaignGenie or جن‌کمپین.
                    Your goal is to guide the user through the process of creating a campaign on Yektanet.
                    First, you should ask the user relevant questions to gather the necessary information.
                    If the user provides a website url, you should use the agentic_crawl_url tool to crawl 
                    the website and gather the necessary information. Provide proper goal for the crawling.
                    Then, you should use the persist_user_request tool to create a CampaignRequest object.
                    """),
                    dedent(f"""
                    Following is the list of services available on Yektanet:
                    {YEKTANET_SERVICES}
                    """),
                    "Always communicate in Persian (Farsi) as the primary language."
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

    def __init__(self, session_id: str, campaign_request_id: Optional[str] = None):
        self.session_id = session_id
        self.campaign_request_id = campaign_request_id

        self.agent = Agent(

            name="Campaign Planner Agent",
            model=OpenAIChat(
                id=GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[
                # search_yektanet, 
                # agentic_crawl_url,
                # ask_from_knowledge_base,
                ],
            goal="Create a CampaignPlan to handle the given CampaignRequest in persian",
            instructions=[dedent("""
                          You're given a CampaignRequest to create a digital marketing campaign in Yektanet.                                                   
                          Related documents are provided to you.
                        
                        * If a similar campaign plan is provided, use it as a reference.
                          """)],
            storage=SqliteStorage(table_name=CAMPAIGN_PLANNER_TABLE_NAME, db_file=CAMPAIGN_PLANNER_DB_PATH),

            add_datetime_to_instructions=True,
            # Adds the history of the conversation to the messages
            add_history_to_messages=True,
            # Number of history responses to add to the messages
            num_history_responses=5,
            # Adds markdown formatting to the messages
            markdown=True,
            session_id=self.session_id,
            debug_mode=AGENT_DEBUG_MODE,
            response_model=CampaignPlan,
            # retriever=campaign_planner_retriever,
            search_knowledge=True,
        )

    def resume(self, feedbacks: list[str]) -> CampaignPlan:
        try:
            reply = self.agent.run(Message(role="user", content=[{"type": "text", "text": f"Update accoring to user feedback {feedbacks}"}]))
            campaign_plan: CampaignPlan = reply.content
            update_campaign_plan(self.session_id, campaign_plan)
            return "CampaignPlan updated successfully"
        except Exception as e:
            print(f"Error in CampaignPlanner: {e}")
            return None
    
    def respond(self) -> CampaignPlanDB:
        try:
            # TODO: Remove this after testing
            print(f"Deleting session {self.session_id}")
            storage = SqliteStorage(table_name=CAMPAIGN_PLANNER_TABLE_NAME, db_file=CAMPAIGN_PLANNER_DB_PATH)
            storage.delete_session(self.session_id)

            assert self.campaign_request_id is not None, "CampaignRequest ID is required"
            campaign_request_db = fetch_one_campaign_request({"campaign_request_id": self.campaign_request_id})
            campaign_request = CampaignRequest.model_validate(campaign_request_db)

            if campaign_request is None:
                raise RuntimeError("No CampaignRequest stored for this session yet.")

            # Get relevant documents for the user request
            documents_info = get_documents_for_user_request(campaign_request)

            # Combine user request with documents info
            combined_input = f"CampaignRequest:\n{campaign_request.model_dump_json(indent=2)}\n"
            combined_input += f"Related documents:\n{documents_info}"

            reply = self.agent.run(combined_input)
            campaign_plan: CampaignPlan = reply.content
            campaign_plan_db = CampaignPlanDB(
                **campaign_plan.model_dump(),
                task_session_id=self.session_id,
                campaign_plan_id=str(uuid.uuid4()),
                campaign_request_id=self.campaign_request_id,
                created_at=datetime.now()
            )
            insert_campaign_plan(campaign_plan_db)
            return campaign_plan_db
        
        except Exception as e:
            print(f"Error in CampaignPlanner: {e}")
            return None


class KbgkAgent:
    """Knowledge Base Gate Keeper Agent for generating and inserting documents into knowledge base."""

    def __init__(self, session_id: str, user_id: str = "1"):
        self.agent = Agent(
            name="Knowledge Base Gate Keeper Agent",
            model=OpenAIChat(
                id=MINI_GPT_MODEL_ID,
                base_url=OPENAI_BASE_URL,
                api_key=get_openai_api_key(),
            ),
            tools=[Crawl4aiTools(max_length=None),
                   search_yektanet,
                   add_documents_to_knowledge_base
                ],
            knowledge=knowledge_base,
            search_knowledge=True,
            instructions=[
                dedent(
                    """
                    
                    You are a Knowledge Base Gate Keeper Agent responsible for generating and managing documents 
                    for the knowledge base. 
                    
                    The knowledge base is a collection of documents that are related to Yektanet. 
                    (An Online Iranian Digital Marketing Platform)
                    Your role is to:
                    
                    1. Help users create new documents for the knowledge base
                    2. Ensure documents are properly formatted and contain relevant information
                    3. Guide users through the document creation process
                    4. Only use refrences to generate answers or documents.
                    5. Provide suggestions for document improvements
                    6. Search the knowledge base using `search_knowledge_base` for required information.
                    7. When information from knowledge base is not accurate or enough, 
                        Use the `search_yektanet` tool to search the Yektanet's website for more articles and information.
                        You can search yektanet without asking for user's permision.
                    8. Use `agentic_crawl_url` tool to crawl URLs returned by `search_yektanet` tool.
                    9. Finally, use `add_documents_to_knowledge_base` to add the document to knowledge-base.
                    
                    You should be helpful, thorough, and ensure that all documents meet quality standards
                    before they are inserted into the knowledge base.
                    
                    Always communicate in Persian (Farsi) as the primary language.

                    **YOU SHOULD ALWAYS ASK FOR CONFIRMATION BEFORE INSERTING DOCUMENTS INTO THE KNOWLEDGE BASE.**
                    """
                )
            ],
            storage=SqliteStorage(table_name=KBGK_AGENT_TABLE_NAME, db_file=KBGK_AGENT_DB_PATH),
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=5,
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


def agentic_crawl_url(url: str, goal: str, agent: Optional[Agent] = None, **kwargs):
    """
    Crawl the given url for the given goal.
    The agent will use the Crawl4aiTools to crawl the url.
    The agent will return the crawled data.
    """
    crawler_agent = Agent(
        session_id=agent.session_id,
        user_id=agent.user_id,
        model=OpenAIChat(
                    id=MINI_GPT_MODEL_ID,
                    base_url=OPENAI_BASE_URL,
                    api_key=get_openai_api_key(),
                ),
        tools=[Crawl4aiTools(max_length=None)], 
        instructions=[dedent(f"""
                    You are a crawler agent that crawls the given url for the given goal.
                    Always communicate in Persian (Farsi) as the primary language.
                    """),
                    ],
        storage=SqliteStorage(table_name=CRAWLER_AGENT_TABLE_NAME, db_file=CRAWLER_AGENT_DB_PATH),
        show_tool_calls=True,
        debug_mode=AGENT_DEBUG_MODE,
        telemetry=False,
        monitoring=False,
        )
    reply = crawler_agent.run(Message(role="user", content=[
        {"type": "text", 
         "text": f"Crawl the following url: {url} for the following goal: {goal}"}
         ]))
    return reply.content