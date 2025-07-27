"""
MongoDB utilities for CampaignGenie application.
Handles database connections and operations for MongoDB.
"""

from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from pages.config import (
    get_mongodb_uri,
    get_mongodb_database,
    get_mongodb_campaign_requests_collection,
    get_mongodb_tasks_collection,
)
from pages.models import CampaignRequestDB, Task


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
    collection = get_mongodb_manager().get_collection(get_mongodb_campaign_requests_collection())
    result = collection.insert_one(campaign_request.model_dump())
    
    return str(result.inserted_id)

def insert_task(task: Task) -> str:
    """
    Insert a Task into the Tasks collection.
    """
    collection = get_mongodb_manager().get_collection(get_mongodb_tasks_collection())
    result = collection.insert_one(task.model_dump())
    return str(result.inserted_id)

def fetch_one_campaign_request(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch campaign requests from MongoDB with optional status filtering.
    
    Args:
        status: Optional status filter (e.g., "new", "in_progress", "completed", "failed")
        
    Returns:
        List of campaign request dictionaries
    """
    collection = get_mongodb_manager().get_collection(get_mongodb_campaign_requests_collection())
        
    # Fetch documents
    document = collection.find_one(query)
    
    # Convert ObjectId to string for JSON serialization
    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]
    
    return document

