import time
from datetime import datetime

from textwrap import dedent
from pages.yektanet_utils import create_native_campaign, generate_ad_image, create_ad

from pages.models import (
    GenerateCampaignPlanTask,
    CreateYektanetCampaignTask,
    CampaignPlanDB,
)
from pages.agents import CampaignPlanner
from pages.kb import add_document_to_knowledge_base
from pages.mongodb_utils import (
    fetch_one_task,
    update_task,
    insert_task,
    fetch_one_campaign_plan,
    update_campaign_plan,
)


class TaskConsumer:
    """Consumes tasks from the task directory and processes them."""

    def process_generate_campaign_plan(self, task: dict) -> None:
        """Process a generate_campaign_plan task using CampaignPlanner agent."""
        try:
            task = GenerateCampaignPlanTask.model_validate(task)
            print(f"Processing campaign plan task for session: {task.session_id}")
            # TODO: Update campaign_request status to in_progress

            if task.status == "confirmed":
                print(f"Creating Yektanet campaign task for session: {task.session_id}")
                create_yektanet_task = CreateYektanetCampaignTask(
                    type="create_yektanet_campaign",
                    description="Create campaign and ads in Yektanet for confirmed campaign plan.",
                    status="new",
                    session_id=task.session_id,
                    created_at=datetime.utcnow(),
                    campaign_plan_id=task.campaign_plan_id,
                    campaign_request_id=task.campaign_request_id,
                )
                insert_task(create_yektanet_task)
                self.add_campaign_plan_to_kb(task)
                task.status = "completed"
            else:
                campaign_planner = CampaignPlanner(
                    session_id=task.session_id,
                    campaign_request_id=task.campaign_request_id,
                )
                if task.status == "new":
                    campaign_plan = campaign_planner.respond()
                elif task.status == "retry_with_feedback":
                    campaign_plan = campaign_planner.resume(task.feedbacks)

                if campaign_plan is None:
                    print(f"Error in CampaignPlanner: {campaign_plan}")
                    task.status = "failed"
                else:
                    print(
                        f"Successfully generated campaign plan for session: {task.session_id}"
                    )
                    task.status = "pending_confirm"
                    task.campaign_plan_id = campaign_plan.campaign_plan_id

        except Exception as e:
            print(
                f"Error processing campaign plan task for session {task.session_id}: {e}"
            )
            task.status = "failed"
        update_task(task)

    def process_create_yektanet_campaign(self, task: dict) -> None:
        """Process a create_yektanet_campaign task."""
        try:
            task = CreateYektanetCampaignTask.model_validate(task)
            campaign_plan = fetch_one_campaign_plan(
                {"campaign_plan_id": task.campaign_plan_id}
            )
            campaign_plan = CampaignPlanDB.model_validate(campaign_plan)
        except Exception as e:
            print(
                f"Error fetching campaign plan for task: {task.campaign_plan_id} error: {e}"
            )
            return
        try:
            if task.status == "new":
                if campaign_plan and campaign_plan.type == "native":
                    created_campaign_id = create_native_campaign(
                        name=campaign_plan.name,
                        daily_budget=campaign_plan.budget,
                        cost_per_click=campaign_plan.bid_toman,
                        page_keywords=campaign_plan.targeting_config.keywords,
                        page_categories=campaign_plan.targeting_config.categories,
                        user_segments=campaign_plan.targeting_config.user_segments,
                        publisher_group_name=campaign_plan.publisher_group,
                    )
                    if created_campaign_id is None:
                        print(
                            f"Failed to create campaign for task: {task.campaign_plan_id}"
                        )
                        task.status = "failed"
                    else:
                        print(f"Created campaign with ID: {created_campaign_id}")
                        task.status = "create_ads"
                        task.created_campaign_id = str(created_campaign_id)
                else:
                    print(f"No campaign plan found for task: {task.campaign_plan_id}")
                    task.status = "failed"
            elif task.status == "create_ads":
                print(f"Creating ads for campaign: {task.created_campaign_id}")
                for ad in campaign_plan.ads_description:
                    if ad.image.source == "generate" and ad.image.image_url is None:
                        ad.image.image_url = generate_ad_image(ad.image.prompt)
                    if ad.image.image_url is None:
                        print(f"Failed to generate image for ad: {ad.title}")
                        task.status = "failed"
                        break
                    if ad.created_ad_id is None:
                        created_ad_id = create_ad(
                            task.created_campaign_id,
                            ad.title,
                            ad.image.image_url,
                            ad.landing_url,
                            ad.call_to_action,
                            ad.image.source
                        )
                        if created_ad_id is None:
                            print(
                                f"Failed to create ad for task: {task.campaign_plan_id}"
                            )
                            task.status = "failed"
                            break
                        else:
                            ad.created_ad_id = str(created_ad_id)
                            task.created_ads.append(ad.created_ad_id)
                if task.created_ads is not None and len(task.created_ads) >= len(
                    campaign_plan.ads_description
                ):
                    task.status = "completed"
                else:
                    task.status = "create_ads"
                    task.retry_count += 1
                if task.retry_count > 5:
                    task.status = "failed"
            else:
                print(f"No campaign plan found for task: {task.campaign_plan_id}")
                task.status = "failed"
        except Exception as e:
            task.retry_count += 1
            if task.retry_count > 5:
                task.status = "failed"
            print(
                f"Error processing create yektanet campaign task for session {task.session_id}: {e}"
            )

        update_task(task)
        update_campaign_plan(campaign_plan)

    def add_campaign_plan_to_kb(self, task: GenerateCampaignPlanTask) -> None:
        """Adds the campaign plan to the knowledge base."""
        try:
            campaign_plan = fetch_one_campaign_plan(
                {"campaign_plan_id": task.campaign_plan_id}
            )
            campaign_plan = CampaignPlanDB.model_validate(campaign_plan)
            if campaign_plan:
                name = f"کمپین پلن {campaign_plan.name} | {campaign_plan.goal}"
                content = dedent(f"""
                    کمپین پلن: {campaign_plan.name}
                    هدف: {campaign_plan.goal}
                    مخاطبین: {campaign_plan.target_audience_description}
                """)
                metadata = {
                    "contenttype": "campaign_plan",
                    "full_text": campaign_plan.model_dump_json(indent=2),
                    "name": name,
                }
                print(name, content, metadata)
                add_document_to_knowledge_base(name, content, metadata)
            else:
                print(f"No campaign plan found for task: {task.campaign_plan_id}")
        except Exception as e:
            print(f"Error adding campaign plan to knowledge base: {e}")

    def run_loop(self, sleep_interval: int = 10) -> None:
        """Main loop that continuously checks for pending tasks and processes them."""
        print(
            f"Starting task consumer loop. Checking tasks every {sleep_interval} seconds..."
        )

        while True:
            try:
                # TODO: get a task with status not one of "completed", "failed", pending_confirm
                task = fetch_one_task(
                    {"status": {"$nin": ["completed", "failed", "pending_confirm"]}}
                )

                if task is not None:
                    print(f"Found a task: {task}")
                    if task["type"] == "generate_campaign_plan":
                        self.process_generate_campaign_plan(task)
                    elif task["type"] == "create_yektanet_campaign":
                        self.process_create_yektanet_campaign(task)
                    else:
                        print(f"Unknown task type: {task.get('type', 'NO_TYPE')}")
                        # TODO: Mark unknown task types as failed
                else:
                    print("No pending tasks found")

                # Sleep before next iteration
                time.sleep(sleep_interval)

            except KeyboardInterrupt:
                print("Task consumer loop interrupted by user")
                break
            except Exception as e:
                print(f"Error in task consumer loop: {e}")
                time.sleep(sleep_interval)


def main():
    """Main function to run the task consumer."""
    consumer = TaskConsumer()
    consumer.run_loop()


if __name__ == "__main__":
    main()
