import streamlit as st
import json
from pathlib import Path
from typing import Optional, List, Tuple

from pages.models import Task, CampaignPlan
from pages.crud import fetch_latest_campaign_plan
from pages.config import get_tasks_dir_path


def read_task_file(file_path: Path) -> Optional[Task]:
    """Read a task from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
            return Task(**task_data)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        st.error(f"Error reading task file {file_path}: {e}")
        return None


def get_pending_confirm_tasks() -> List[Tuple[Path, Task]]:
    """Get all pending confirm_campaign_plan tasks from the task directory."""
    tasks_dir = Path(get_tasks_dir_path())
    pending_tasks = []
    
    if not tasks_dir.exists():
        return pending_tasks
    
    for file_path in tasks_dir.glob("*.json"):
        task = read_task_file(file_path)
        if task and task.type == "confirm_campaign_plan" and task.status == "pending":
            pending_tasks.append((file_path, task))
    
    return pending_tasks


def format_task_display_name(task: Task, file_path: Path, business_name: Optional[str] = None) -> str:
    """Format a task for display in the dropdown."""
    # Get file creation time for additional context
    try:
        creation_time = file_path.stat().st_ctime
        from datetime import datetime
        time_str = datetime.fromtimestamp(creation_time).strftime("%m/%d %H:%M")
    except:
        time_str = "Unknown"
    
    business_part = f" | Business: {business_name}" if business_name else ""
    return f"[{time_str}] Session: {task.session_id[:8]}...{business_part} | {task.description[:50]}{'...' if len(task.description) > 50 else ''}"


def update_task_status(file_path: Path, status: str, feedback: str = "") -> None:
    """Update the status of a task in its JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        task_data['status'] = status
        if feedback:
            if task_data['feedbacks'] is None:
                task_data['feedbacks'] = []
            task_data['feedbacks'].append(feedback)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
            
    except (json.JSONDecodeError, IOError) as e:
        st.error(f"Error updating task status in {file_path}: {e}")


def display_campaign_plan(plan: CampaignPlan) -> None:
    """Display a campaign plan in a formatted way."""
    st.header("📋 Campaign Plan Details")
    
    # Basic Information
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Campaign Type", plan.type.title())
        st.metric("Daily Budget", f"{plan.budget:,} تومان")
        st.metric("Bid Amount", f"{plan.bid_toman:,} تومان")
    
    with col2:
        st.metric("Bidding Strategy", plan.bidding_strategy.upper())
        st.metric("Campaign Name", plan.name)
    
    # Campaign Details
    st.subheader("📝 Campaign Information")
    st.write("**Business Description:**")
    st.info(plan.business_description)
    
    st.write("**Campaign Description:**")
    st.info(plan.description)
    
    st.write("**Target Audience:**")
    st.info(plan.target_audience_description)
    
    # Targeting Configuration
    st.subheader("🎯 Targeting Configuration")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Keywords:**")
        for keyword in plan.targetign_config.keywords:
            st.write(f"• {keyword}")
    
    with col2:
        st.write("**User Segments:**")
        for segment in plan.targetign_config.user_segments:
            st.write(f"• {segment}")
    
    with col3:
        st.write("**Categories:**")
        for category in plan.targetign_config.categories:
            st.write(f"• {category}")
    
    # Ads Description
    if plan.ads_description:
        st.subheader("📢 Ads Description")
        for i, ad_desc in enumerate(plan.ads_description, 1):
            st.write(f"**Ad {i}:**")
            st.info(ad_desc)


def main():
    st.set_page_config(
        page_title="Campaign Plan Approval",
        page_icon="✅",
        layout="wide"
    )
    
    # --- Task selection at the very top ---
    pending_tasks = get_pending_confirm_tasks()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 Select Task to Review")
        st.info(f"Found {len(pending_tasks)} pending confirmation tasks")
        # Prepare dropdown options with business name
        task_options = []
        task_mapping = {}
        for file_path, task in pending_tasks:
            plan = fetch_latest_campaign_plan(task.session_id)
            business_name = plan.name if plan else None
            display_name = format_task_display_name(task, file_path, business_name)
            task_options.append(display_name)
            task_mapping[display_name] = (file_path, task, plan)
        if task_options:
            default_index = 0
            selected_task_display = st.selectbox(
                "Choose a task to review:",
                options=task_options,
                index=default_index,
                help="Select a pending campaign plan confirmation task to review"
            )
    with col2:
        st.subheader("🔄 Refresh")
        if st.button("Refresh Tasks", use_container_width=True):
            st.rerun()
    
    st.title("✅ Campaign Plan Approval System")
    st.markdown("---")
    
    if not pending_tasks or not task_options:
        st.warning("No pending campaign plan confirmation tasks found.")
        st.info("Tasks will appear here when campaign plans are ready for approval.")
        return
    
    # Get the selected task, task file, and plan
    task_file_path, task, campaign_plan = task_mapping[selected_task_display]
    
    # Task details section
    st.markdown("---")
    st.subheader("📄 Task Details")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Session ID", task.session_id[:12] + "...")
    with col2:
        st.metric("Task Type", task.type.replace("_", " ").title())
    with col3:
        st.metric("Status", task.status.title())
    
    st.write("**Description:**")
    st.info(task.description)
    
    if not campaign_plan:
        st.error(f"No campaign plan found for session: {task.session_id}")
        st.info("The campaign plan may still be in progress or failed to generate.")
        return
    
    # Display the campaign plan
    display_campaign_plan(campaign_plan)
    
    st.markdown("---")
    
    # Approval section
    st.subheader("🔍 Review & Decision")
    
    # Feedback text area
    feedback = st.text_area(
        "Feedback (Optional):",
        placeholder="Enter any feedback, suggestions, or reasons for rejection...",
        height=100
    )
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Confirm Campaign Plan", type="primary", use_container_width=True):
            update_task_status(task_file_path, "completed_add_to_kb", feedback)
            st.success("Campaign plan confirmed successfully!")
            st.rerun()
    
    with col2:
        if st.button("❌ Reject Campaign Plan", type="secondary", use_container_width=True):
            if not feedback.strip():
                st.error("Please provide feedback when rejecting a campaign plan.")
            else:
                update_task_status(task_file_path, "retry_with_feedback", feedback)
                st.error("Campaign plan rejected.")
                st.rerun()
    
    with col3:
        st.info("💡 **Note:** Rejecting requires feedback. Confirming is optional.")


if __name__ == "__main__":
    main() 