"""
MongoDB utilities for CampaignGenie application.
Handles database connections and operations for MongoDB.
"""

from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson import ObjectId

from pages.config import (
    get_mongodb_uri,
    get_mongodb_database,
    get_mongodb_campaign_requests_collection,
    get_mongodb_tasks_collection,
    get_mongodb_campaign_plans_collection,
)
from pages.models import CampaignRequestDB, Task, CampaignPlanDB


class MongoDBManager:
    """Manages MongoDB connections."""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(get_mongodb_uri())
            self.database = self.client[get_mongodb_database()]
            print(f"Connected to MongoDB: {get_mongodb_uri()}")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection by name."""
        if self.database is None:
            self.connect()
        return self.database[collection_name]


# Global MongoDB manager instance
mongodb_manager = MongoDBManager()


def get_mongodb_manager() -> MongoDBManager:
    """Get the global MongoDB manager instance."""
    return mongodb_manager


def insert_campaign_request(campaign_request: CampaignRequestDB) -> str:
    """
    Insert a CampaignRequest into the CampaignRequests collection.

    Args:
        campaign_request: The CampaignRequestDB object to insert

    Returns:
        str: The inserted document's ID
    """
    collection = get_mongodb_manager().get_collection(
        get_mongodb_campaign_requests_collection()
    )
    result = collection.insert_one(campaign_request.model_dump())

    return str(result.inserted_id)


def insert_task(task: Task) -> str:
    """
    Insert a Task into the Tasks collection.
    """
    collection = get_mongodb_manager().get_collection(get_mongodb_tasks_collection())
    result = collection.insert_one(task.model_dump())
    return str(result.inserted_id)


def update_task(task: Task) -> None:
    """
    Update a Task in the Tasks collection.
    """
    assert task.id is not None, "Task ID is required"
    collection = get_mongodb_manager().get_collection(get_mongodb_tasks_collection())
    task_dict = task.model_dump()
    task_dict.pop("id")
    collection.update_one({"_id": ObjectId(task.id)}, {"$set": task_dict})


def insert_campaign_plan(campaign_plan: CampaignPlanDB) -> str:
    """
    Insert a CampaignPlan into the CampaignPlans collection.
    """
    collection = get_mongodb_manager().get_collection(
        get_mongodb_campaign_plans_collection()
    )
    result = collection.insert_one(campaign_plan.model_dump())
    return str(result.inserted_id)


def update_campaign_plan(campaign_plan: CampaignPlanDB) -> None:
    """
    Update a CampaignPlan in the CampaignPlans collection.
    """
    assert campaign_plan.id is not None, "CampaignPlan ID is required"
    collection = get_mongodb_manager().get_collection(
        get_mongodb_campaign_plans_collection()
    )
    campaign_plan_dict = campaign_plan.model_dump()
    campaign_plan_dict.pop("id")
    collection.update_one(
        {"_id": ObjectId(campaign_plan.id)}, {"$set": campaign_plan_dict}
    )


def fetch_one_campaign_request(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch campaign requests from MongoDB with optional status filtering.

    Args:
        status: Optional status filter (e.g., "new", "in_progress",
        "completed", "failed")

    Returns:
        List of campaign request dictionaries
    """
    collection = get_mongodb_manager().get_collection(
        get_mongodb_campaign_requests_collection()
    )

    # Fetch documents
    document = collection.find_one(query)

    # Convert ObjectId to string for JSON serialization
    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]

    return document


def fetch_one_task(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch one task from MongoDB with optional query filtering.

    Args:
        query: Optional query to fetch one task

    Returns:
        Task dictionary
    """
    collection = get_mongodb_manager().get_collection(get_mongodb_tasks_collection())

    # Fetch documents
    document = collection.find_one(query)
    if document is None:
        return None

    # Convert ObjectId to string for JSON serialization
    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]

    return document


def fetch_one_campaign_plan(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch one campaign plan from MongoDB with optional query filtering.
    """
    collection = get_mongodb_manager().get_collection(
        get_mongodb_campaign_plans_collection()
    )
    document = collection.find_one(query)
    if document is None:
        return None
    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]
    return document


def fetch_tasks(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch tasks from MongoDB with optional query filtering.
    """
    collection = get_mongodb_manager().get_collection(get_mongodb_tasks_collection())
    documents = list(collection.find(query))
    for document in documents:
        if "_id" in document:
            document["id"] = str(document["_id"])
            del document["_id"]
    return documents
