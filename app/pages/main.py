# from pages.agents import CampaignPlanner
from pages.crud import fetch_campaign_requests


if __name__ == "__main__":
    # planner = CampaignPlanner(session_id="ddcc2f23-41ee-4709-b6a8-28dfa0d1c1d0")
    # planner.respond()
    print([dict(d) for d in fetch_campaign_requests()])