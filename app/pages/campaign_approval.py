import streamlit as st
import json
from pathlib import Path
from typing import Optional, List, Tuple

from pages.models import GenerateCampaignPlanTask, CampaignPlanDB
from pages.yektanet_utils import generate_ad_image
from pages.mongodb_utils import (
    fetch_tasks,
    fetch_one_campaign_plan,
    update_task,
    update_campaign_plan,
)


def get_pending_confirm_tasks() -> List[GenerateCampaignPlanTask]:
    """Get all pending confirm_campaign_plan tasks from the task directory."""
    pending_tasks = fetch_tasks({"status": "pending_confirm"})
    tasks = [GenerateCampaignPlanTask.model_validate(task) for task in pending_tasks]
    return tasks


def format_task_display_name(
    task: GenerateCampaignPlanTask, name: Optional[str] = None
) -> str:
    """Format a task for display in the dropdown."""
    time_str = task.created_at.strftime("%m/%d %H:%M")
    return f"[{time_str}] Session: {task.session_id[:8]}... | Name: {name}"


def update_task_status(file_path: Path, status: str, feedback: str = "") -> None:
    """Update the status of a task in its JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)

        task_data["status"] = status
        if feedback:
            if task_data["feedbacks"] is None:
                task_data["feedbacks"] = []
            task_data["feedbacks"].append(feedback)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)

    except (json.JSONDecodeError, IOError) as e:
        st.error(f"Error updating task status in {file_path}: {e}")


def display_campaign_plan(plan: CampaignPlanDB) -> None:
    """Display a campaign plan in a formatted way."""
    st.header("📋 Campaign Plan Details")

    # Initialize session state for generated images if not exists
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = {}

    # Basic Information
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Campaign Type", plan.type.title())
        st.metric("Daily Budget", f"{plan.budget:,} تومان")
        st.metric("Bid Amount", f"{plan.bid_toman:,} تومان")

    with col2:
        st.metric("Bidding Strategy", plan.bidding_strategy.upper())
        st.metric("Campaign Name", plan.name)
        st.metric("Publisher Group", plan.publisher_group)

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
        for keyword in plan.targeting_config.keywords:
            st.write(f"• {keyword}")

    with col2:
        st.write("**User Segments:**")
        for segment in plan.targeting_config.user_segments:
            st.write(f"• {segment}")

    with col3:
        st.write("**Categories:**")
        for category in plan.targeting_config.categories:
            st.write(f"• {category}")

    # Ads Description
    if plan.ads_description:
        st.subheader("📢 Ads Description")
        for i, ad_desc in enumerate(plan.ads_description, 1):
            st.write(f"**Ad {i}:**")

            # Create columns for better layout
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Title:**")
                st.info(ad_desc.title)
                st.write("**Landing URL:**")
                st.info(ad_desc.landing_url)

            with col2:
                st.write("**Call to Action:**")
                st.info(ad_desc.call_to_action)
                st.write("**Image Description:**")
                st.info(ad_desc.image.prompt)

            with col3:
                # Display existing image if available
                if ad_desc.image.image_url is not None:
                    st.write("**Existing Image:**")
                    st.image(
                        ad_desc.image.image_url,
                        caption=f"Existing image for Ad {i}",
                        use_container_width=True,
                    )
                else:
                    st.write("**No existing image available**")

                # Generate Image button and display
                image_key = f"ad_{i}_image"

                # Check if image already generated
                if image_key in st.session_state.generated_images:
                    st.success("✅ Image generated successfully!")
                    st.image(
                        st.session_state.generated_images[image_key],
                        caption=f"Generated image for Ad {i}",
                        use_container_width=True,
                    )

                    # Save as ad image button
                    if st.button("💾 Save as Ad Image", key=f"save_btn_{i}"):
                        # Update the ad description with the generated image
                        ad_desc.image.image_url = st.session_state.generated_images[
                            image_key
                        ]
                        update_campaign_plan(plan)
                        st.success("✅ Image saved as ad image!")
                else:
                    if st.button("Generate Image", key=f"generate_btn_{i}"):
                        with st.spinner("Generating image..."):
                            try:
                                image_path = generate_ad_image(ad_desc.image.prompt)
                                if (
                                    image_path
                                    and image_path != "Failed to generate ad image."
                                ):
                                    st.session_state.generated_images[image_key] = (
                                        image_path
                                    )
                                    st.success("✅ Image generated successfully!")
                                    st.image(
                                        image_path,
                                        caption=f"Generated image for Ad {i}",
                                        use_container_width=True,
                                        width=300,
                                    )

                                    # Save as ad image button for newly generated image
                                    if st.button(
                                        "💾 Save as Ad Image", key=f"save_new_btn_{i}"
                                    ):
                                        # Update the ad description with the generated image
                                        ad_desc.image.image_url = image_path
                                        update_campaign_plan(plan)
                                        st.success("✅ Image saved as ad image!")
                                else:
                                    st.error(
                                        "❌ Failed to generate image. Please try again."
                                    )
                            except Exception as e:
                                st.error(f"❌ Error generating image: {str(e)}")

            st.markdown("---")


def main():
    st.set_page_config(
        page_title="Campaign Plan Approval", page_icon="✅", layout="wide"
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
        for task in pending_tasks:
            plan_db = fetch_one_campaign_plan(
                {"campaign_plan_id": task.campaign_plan_id}
            )
            plan = CampaignPlanDB.model_validate(plan_db)
            name = plan.name if plan else None
            display_name = format_task_display_name(task, name)
            task_options.append(display_name)
            task_mapping[display_name] = (task, plan)
        if task_options:
            default_index = 0
            selected_task_display = st.selectbox(
                "Choose a task to review:",
                options=task_options,
                index=default_index,
                help="Select a pending campaign plan confirmation task to review",
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
    task, campaign_plan = task_mapping[selected_task_display]

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
        height=100,
    )

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button(
            "✅ Confirm Campaign Plan", type="primary", use_container_width=True
        ):
            task.status = "confirmed"
            update_task(task)
            st.success("Campaign plan confirmed successfully!")
            st.rerun()

    with col2:
        if st.button(
            "❌ Reject Campaign Plan", type="secondary", use_container_width=True
        ):
            if not feedback.strip():
                st.error("Please provide feedback when rejecting a campaign plan.")
            else:
                task.status = "retry_with_feedback"
                if task.feedbacks is None:
                    task.feedbacks = []
                task.feedbacks.append(feedback)
                update_task(task)
                st.error("Campaign plan rejected.")
                st.rerun()

    with col3:
        st.info("💡 **Note:** Rejecting requires feedback. Confirming is optional.")


if __name__ == "__main__":
    main()
