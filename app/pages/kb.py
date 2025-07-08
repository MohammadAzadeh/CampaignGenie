import os
import pandas as pd

from typing import Optional

from agno.agent import Agent
from agno.knowledge.document import DocumentKnowledgeBase
from agno.document import Document
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder
from models import UserRequest

# TODO: Move all Storage Config to a file
documents_df = pd.read_csv("pages/files/CampaignGenieDocuments - Documents.csv")

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
        table_name="recipes",
        uri="pages/files/tmp/lancedb",
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(
            id="text-embedding-3-small",
            base_url="https://api.metisai.ir/openai/v1",
            api_key=os.environ["METIS_API_KEY"],
        ),
    ),
)


# Uncomment to load documents again.
# knowledge_base.load(recreate=True)


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


def get_documents_for_user_request(user_request: UserRequest) -> str:
    """
    Retrieve relevant documents based on business_detail and goal fields from UserRequest.
    Generate a formatted message with top 10 documents including names and content types.
    
    Args:
        user_request (UserRequest): The user request containing business details and goal
        
    Returns:
        str: Formatted message containing document information
    """
    try:
        # Create a comprehensive search query from business details and goal
        business_name = user_request.business_detail.name
        business_type = user_request.business_detail.type
        business_description = user_request.business_detail.description or ""
        goal = user_request.goal
        
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
