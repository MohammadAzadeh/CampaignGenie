import time
from datetime import datetime

from textwrap import dedent

from pages.models import GenerateCampaignPlanTask, CreateYektanetCampaignTask, CampaignPlan
from pages.agents import CampaignPlanner
from pages.kb import add_document_to_knowledge_base
from pages.mongodb_utils import fetch_one_task, update_task, insert_task, fetch_one_campaign_plan


class TaskConsumer:
    """Consumes tasks from the task directory and processes them."""

    def process_campaign_plan_task(self, task: dict) -> None:
        """Process a generate_campaign_plan task using CampaignPlanner agent."""
        try:
            task = GenerateCampaignPlanTask.model_validate(task)
            print(f"Processing campaign plan task for session: {task.session_id}")

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
                # TODO: Update campaign_request status
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
        # TODO: Update campaign_request status

    def add_campaign_plan_to_kb(self, task: GenerateCampaignPlanTask) -> None:
        """Adds the campaign plan to the knowledge base."""
        try:
            campaign_plan = fetch_one_campaign_plan({"campaign_plan_id": task.campaign_plan_id})
            campaign_plan = CampaignPlan.model_validate(campaign_plan)
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
                # get a task with status "new", "retry_with_feedback", "confirmed"
                task = fetch_one_task(
                    {"status": {"$in": ["new", "retry_with_feedback", "confirmed"]}}
                )

                if task is not None:
                    print(f"Found a task: {task}")
                    if task["type"] == "generate_campaign_plan":
                        self.process_campaign_plan_task(task)
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
