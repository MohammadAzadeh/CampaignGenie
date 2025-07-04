import os
import pandas as pd

from typing import Optional

from agno.agent import Agent
from agno.knowledge.document import DocumentKnowledgeBase
from agno.document import Document
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder

# TODO: Move all Storage Config to a file
agent_storage: str = "pages/files/tmp/agents.db"
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
        query: str, agent: Optional[Agent] = None, num_documents: int = 5, **kwargs
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
        case_studies = knowledge_base.search(query=query, num_documents=1, filters={"contenttype": "casestudy"})
        case_studies = [cs.to_dict() for cs in case_studies]
        return case_studies
    except Exception as e:
        print(f"Error during vector database search: {str(e)}")
        return None
