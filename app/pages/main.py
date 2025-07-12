# # from pages.agents import CampaignPlanner
from pages.crud import fetch_campaign_requests
from pages.kb import knowledge_base
from pages.models import CampaignPlan, CampaignConfig

if __name__ == "__main__":
    # planner = CampaignPlanner(session_id="ddcc2f23-41ee-4709-b6a8-28dfa0d1c1d0")
    # planner.respond()
    # print([dict(d) for d in fetch_campaign_requests()])
    print(knowledge_base.documents)


# from pages.agents import FirstAgent
# session_id = "9a0b50eb-6d5d-4272-a660-208638303e6e"
# agent = FirstAgent(session_id=session_id)
# # print(agent.respond("من کی هستم؟"))
# # agent.agent.reset_session_state()
# agent.agent.initialize_agent()
# # agent.agent._initialize_session_state(user_id="1", session_id=session_id)
# agent.agent.read_from_storage(session_id=session_id)
# # print(agent.agent.get_messages_for_session())             789

