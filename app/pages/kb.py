import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional, List, Dict

from agno.knowledge.document import DocumentKnowledgeBase
from agno.document import Document
from agno.vectordb.chroma import ChromaDb
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
        "name": row.get("name"),
        "full_text": row.get("full_text"),
    }

    doc = Document(id=row.get("id"), name=row.get("name"), content=row.get("content"), meta_data=metadata)
    documents.append(doc)

knowledge_base = DocumentKnowledgeBase(
    documents=documents,
    vector_db=ChromaDb(
        collection=VECTOR_DB_TABLE_NAME,
        path=get_vector_db_uri(),
        persistent_client=True,
        embedder=OpenAIEmbedder(
            id=EMBEDDING_MODEL_ID,
            base_url=OPENAI_BASE_URL,
            api_key=get_openai_api_key(),
        ),
    ),
)


def add_documents_to_knowledge_base(name: str, content: str, meta_data: dict):
    """
    Add a document to the knowledge base.
    Args:
        name (str): The name of the document
        content (str): The content of the document, this field to embedded and is used later for retrieval. 
        It should contain unique and meaningful words and expressions that best describe the full_text.
        meta_data (dict): The metadata of the document. It must have following keys:
            - contenttype: The type of the content. One of "casestudy" or "help".(Ask user explicitly)
            - full_text: The full text of the document.
            - url(optional): The reference url of the document.

    Returns:
        str: result of function, either success or error.
    Arg"""
    try:
        id = len(knowledge_base.documents) + 1
        doc = Document(id=id, name=name, content=content, meta_data=meta_data)
        knowledge_base.add_document_to_knowledge_base(doc)
        return "Document added to knowledge base successfully"
    except Exception as e:
        return f"Error in adding document to knowledge base: {str(e)}"


def campaign_planner_retriever(
    query: str, num_documents: int = 2
) -> Optional[list[dict]]:
    """
    Custom retriever function to search the vector database for relevant documents.

    Args:
        query (str): The search query string

    Returns:
        Optional[list[dict]]: List of retrieved documents or None if search fails
    """
    try:
        case_studies = knowledge_base.search(query=query, num_documents=2, filters={"contenttype": "casestudy"})
        helps = knowledge_base.search(query=query, num_documents=2, filters={"contenttype": "help"})
        sample_campaign_plans = knowledge_base.search(query=query, num_documents=1, filters={"contenttype": "campaign_plan"})   
        print("len", len(case_studies), len(helps), len(sample_campaign_plans))
        documents = case_studies + helps + sample_campaign_plans
        documents = [doc.to_dict() for doc in documents]
        return documents
    except Exception as e:
        print(f"Error during vector database search: {str(e)}")
        return f"Error during vector database search: {str(e)}"


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
        # business_description = campaign_request.business.description or ""
        goal = campaign_request.goal
        
        # Build search query combining business info and goal
        search_query = f"{business_type} {business_name} {goal}"
        
        case_studies = knowledge_base.search(query=search_query, num_documents=2, filters={"contenttype": "casestudy"})
        helps = knowledge_base.search(query=search_query, num_documents=2, filters={"contenttype": "help"})
        sample_campaign_plans = knowledge_base.search(query=search_query, num_documents=2, filters={"contenttype": "campaign_plan"})  
        
        documents = case_studies + helps + sample_campaign_plans

        if not documents:
            return "No documents found"
        
        # Generate formatted message with document information
        message_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_dict = doc.to_dict()
            name = doc_dict.get('meta_data', {}).get('name', 'نامشخص')
            content_type = doc_dict.get('meta_data', {}).get('contenttype', 'نامشخص')
            full_text = doc_dict.get('meta_data', {}).get('full_text', 'نامشخص')
            message_parts.append(f"{i}. {name} ({content_type}) \n {full_text}")
        
        return "\n=====\n".join(message_parts)
        
    except Exception as e:
        print(f"Error during document retrieval: {str(e)}")
        return "Error during document retrieval"


def search_yektanet(query: str) -> List[Dict[str, str]]:
    """
    Search Yektanet for the given query and return top 10 results.
    
    Args:
        query (str): The search query to look for on Yektanet
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing 'title' and 'url' for each result
    """
    try:
        # Encode the query for URL
        encoded_query = quote_plus(query)
        search_url = f"https://www.yektanet.com/search/?q={encoded_query}"
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make the request
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        
        # Look for search result elements - this will need to be adjusted based on Yektanet's actual HTML structure
        # Common selectors for search results
        possible_selectors = [
            '.search-result',
            '.result',
            '.search-item',
            '.item',
            'article',
            '.post',
            '.entry'
        ]
        
        search_results = []
        for selector in possible_selectors:
            search_results = soup.select(selector)
            if search_results:
                break
        
        # If no specific selectors work, try to find links that might be search results
        if not search_results:
            # Look for links that contain the search query or are likely to be search results
            all_links = soup.find_all('a', href=True)
            search_results = [link.parent for link in all_links if any(word in link.get_text().lower() for word in query.lower().split())]
        
        # Extract title and URL from each result
        for i, result in enumerate(search_results[:10]):  # Limit to top 10
            # Try to find the title
            title_element = result.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'span', 'div'])
            title = title_element.get_text().strip() if title_element else f"Result {i+1}"
            
            # Clean the title: remove extra whitespace, newlines, and normalize spaces
            if title:
                # Remove extra whitespace and newlines
                title = ' '.join(title.split())
                # Remove any leading/trailing whitespace
                title = title.strip()
            
            # Try to find the URL
            link_element = result.find('a', href=True)
            url = link_element['href'] if link_element else ""
            
            # Make sure URL is absolute
            if url and not url.startswith('http'):
                if url.startswith('/'):
                    url = f"https://www.yektanet.com{url}"
                else:
                    url = f"https://www.yektanet.com/{url}"
            
            if title and url:
                results.append({
                    'title': title,
                    'url': url
                })
        
        return results
        
    except requests.RequestException as e:
        print(f"Error making request to Yektanet: {str(e)}")
        return []
    except Exception as e:
        print(f"Error parsing Yektanet search results: {str(e)}")
        return []



# Uncomment to load documents again.
# knowledge_base.load(recreate=False)


# print(knowledge_base.search(query="مدیریت کاربران", num_documents=1)[0].meta_data["name"])