import os
import json
import time
from typing import List, Optional
from pathlib import Path

from pages.models import Task
from pages.agents import CampaignPlanner
from pages.config import get_tasks_dir_path
from pages.kb import knowledge_base
from pages.crud import fetch_latest_campaign_plan
from agno.document import Document

class TaskConsumer:
    """Consumes tasks from the task directory and processes them."""
    
    def __init__(self):
        self.tasks_dir = Path(get_tasks_dir_path())
        self.tasks_dir.mkdir(exist_ok=True)
    
    def read_task_file(self, file_path: Path) -> Optional[Task]:
        """Read a task from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                return Task(**task_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error reading task file {file_path}: {e}")
            return None
    
    def update_task_status(self, file_path: Path, status: str) -> None:
        """Update the status of a task in its JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            task_data['status'] = status
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error updating task status in {file_path}: {e}")
    
    def get_pending_tasks(self) -> List[tuple[Path, Task]]:
        """Get all pending tasks from the task directory."""
        pending_tasks = []
        
        if not self.tasks_dir.exists():
            return pending_tasks
        
        for file_path in self.tasks_dir.glob("*.json"):
            task = self.read_task_file(file_path)
            if (
                task and task.status == "pending" 
                or task.status == "retry_with_feedback" 
                or task.status == "completed_add_to_kb"):
                pending_tasks.append((file_path, task))
        
        return pending_tasks
    
    def process_campaign_plan_task(self, file_path: Path, task: Task) -> None:
        """Process a generate_campaign_plan task using CampaignPlanner agent."""
        try:
            print(f"Processing campaign plan task for session: {task.session_id}")
            
            # Update task status to in_progress
            self.update_task_status(file_path, "in_progress")
            
            # Create CampaignPlanner agent and process the task
            campaign_planner = CampaignPlanner(session_id=task.session_id)
  
            result = campaign_planner.respond()
            
            if result is None:
                print(f"Error in CampaignPlanner")
                self.update_task_status(file_path, "failed")
            else:
                print(f"Successfully generated campaign plan for session: {task.session_id}")
                self.update_task_status(file_path, "completed")
            
        except Exception as e:
            print(f"Error processing campaign plan task for session {task.session_id}: {e}")
            # Update task status to failed
            self.update_task_status(file_path, "failed")


    def resume_campaign_plan_task(self, file_path: Path, task: Task) -> None:
        """Resumes a generate_campaign_plan task using CampaignPlanner agent."""
        try:
            print(f"Processing campaign plan task for session: {task.session_id}")
            
            # Create CampaignPlanner agent and process the task
            campaign_planner = CampaignPlanner(session_id=task.session_id)
            result = campaign_planner.resume(task.feedbacks)
            
            if result is None:
                print(f"Error in CampaignPlanner")
                # self.update_task_status(file_path, "failed")
            else:
                print(f"Successfully generated campaign plan for session: {task.session_id}")
                self.update_task_status(file_path, "pending")
            
        except Exception as e:
            print(f"Error processing campaign plan task for session {task.session_id}: {e}")
            # Update task status to failed
            self.update_task_status(file_path, "failed")

    def add_campaign_plan_to_kb(self, task: Task) -> None:
        """Adds the campaign plan to the knowledge base."""
        try:
            campaign_plan = fetch_latest_campaign_plan(task.session_id)
            if campaign_plan:
                name = f"کمپین پلن {campaign_plan.name} | {campaign_plan.goal}"
                content = f"""
                    کمپین پلن: {campaign_plan.name}
                    هدف: {campaign_plan.goal}
                    مخاطبین: {campaign_plan.target_audience_description}
                """
                metadata = {
                    "contenttype": 'campaign_plan',
                    "url": None,
                    "full_text": campaign_plan.model_dump_json(),
                }
                id = len(knowledge_base.documents) + 1
                doc = Document(id=id, name=name, content=content, meta_data=metadata)
                print(doc)
                knowledge_base.add_document_to_knowledge_base(doc)
        except Exception as e:
            print(f"Error adding campaign plan to knowledge base: {e}")


    def run_loop(self, sleep_interval: int = 10) -> None:
        """Main loop that continuously checks for pending tasks and processes them."""
        print(f"Starting task consumer loop. Checking tasks every {sleep_interval} seconds...")
        print(f"Monitoring task directory: {self.tasks_dir}")
        
        while True:
            try:
                # Get all pending tasks
                pending_tasks = self.get_pending_tasks()
                
                if pending_tasks:
                    print(f"Found {len(pending_tasks)} pending tasks")
                    
                    for file_path, task in pending_tasks:
                        print(f"Processing task: {task.type} for session: {task.session_id}")
                        
                        if task.type == "generate_campaign_plan":
                            self.process_campaign_plan_task(file_path, task)
                        elif task.type == "confirm_campaign_plan":
                            if task.status == "retry_with_feedback":
                                self.resume_campaign_plan_task(file_path, task)
                            elif task.status == "completed_add_to_kb":
                                self.add_campaign_plan_to_kb(task)
                                self.update_task_status(file_path, "completed")
                        else:
                            print(f"Unknown task type: {task.type}")
                            # Mark unknown task types as failed
                            # self.update_task_status(file_path, "failed")
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
