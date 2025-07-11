import os
import pandas as pd

from typing import Optional

from agno.agent import Agent
from agno.knowledge.document import DocumentKnowledgeBase
from agno.document import Document
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder
from pages.models import CampaignRequest
from pages.config import (
    get_documents_csv_path,
    get_vector_db_uri,
    VECTOR_DB_TABLE_NAME,
    OPENAI_BASE_URL,
    get_openai_api_key,
    EMBEDDING_MODEL_ID,
)

# Load documents from CSV file
documents_df = pd.read_csv(get_documents_csv_path())

# Create Document instances
documents = []
for _, row in documents_df.iterrows():
    metadata = {
        "contenttype": row.get("metadata_contenttype"),
        "url": row.get("metadata_url"),
        "full_text": row.get("full_text"),
    }

    doc = Document(id=row.get("id"), name=row.get("name"), content=row.get("content"), meta_data=metadata)
    documents.append(doc)

knowledge_base = DocumentKnowledgeBase(
    documents=documents,
    vector_db=LanceDb(
        table_name=VECTOR_DB_TABLE_NAME,
        uri=get_vector_db_uri(),
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(
            id=EMBEDDING_MODEL_ID,
            base_url=OPENAI_BASE_URL,
            api_key=get_openai_api_key(),
        ),
    ),
)


# Uncomment to load documents again.
# knowledge_base.load(recreate=False)


def campaign_planner_retriever(
    query: str, agent: Optional[Agent] = None, **kwargs
) -> Optional[list[dict]]:
    """
    Custom retriever function to search the vector database for relevant documents.

    Args:
        query (str): The search query string
        agent (Agent): The agent instance making the query
        num_documents (int): Number of documents to retrieve (default: 5)
        **kwargs: Additional keyword arguments

    Returns:
        Optional[list[dict]]: List of retrieved documents or None if search fails
    """
    try:
        case_studies = knowledge_base.search(query=query, num_documents=2, filters={"contenttype": "casestudy"})
        helps = knowledge_base.search(query=query, num_documents=2, filters={"contenttype": "help"})
        print("len", len(case_studies), len(helps))
        # TODO: Add the name and metadata['contenttype'] of top 10 documents to the response
        documents = case_studies + helps
        documents = [doc.to_dict() for doc in documents]
        return documents
    except Exception as e:
        print(f"Error during vector database search: {str(e)}")
        return None


def get_documents_for_user_request(campaign_request: CampaignRequest) -> str:
    """
    Retrieve relevant documents based on business_detail and goal fields from CampaignRequest.
    Generate a formatted message with top 10 documents including names and content types.
    
    Args:
        campaign_request (CampaignRequest): The request containing business details and goal
        
    Returns:
        str: Formatted message containing document information
    """
    try:
        # Create a comprehensive search query from business details and goal
        business_name = campaign_request.business.name
        business_type = campaign_request.business.type
        business_description = campaign_request.business.description or ""
        goal = campaign_request.goal
        
        # Build search query combining business info and goal
        search_query = f"{business_name} {business_type} {business_description} {goal}"
        
        # Search for relevant documents (top 10)
        documents = knowledge_base.search(query=search_query, num_documents=10)
        
        if not documents:
            return "No documents found"
        
        # Generate formatted message with document information
        message_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_dict = doc.to_dict()
            name = doc_dict.get('name', 'نامشخص')
            content_type = doc_dict.get('meta_data', {}).get('contenttype', 'نامشخص')
            
            message_parts.append(f"{i}. {name} ({content_type})")
        
        return "\n".join(message_parts)
        
    except Exception as e:
        print(f"Error during document retrieval: {str(e)}")
        return "Error during document retrieval"
