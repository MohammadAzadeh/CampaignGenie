"""
Configuration settings for CampaignGenie application.
Centralized configuration for database paths, file paths, API settings, and other configurable values.
"""

import os
import pathlib
from typing import Optional

# ============================================================================
# Database Configuration
# ============================================================================

# Main SQLite database path
DB_PATH = pathlib.Path("app/pages/files/campaign_genie.db")

# Agent storage database paths
FIRST_AGENT_DB_PATH = "app/pages/files/campaign_genie.db"
CAMPAIGN_PLANNER_DB_PATH = "app/pages/files/campaign_genie.db"
KBGK_AGENT_DB_PATH = "app/pages/files/campaign_genie.db"
CRAWLER_AGENT_DB_PATH = "app/pages/files/campaign_genie.db"

# Vector database configuration
VECTOR_DB_URI = "app/pages/files/tmp/chromadb"
VECTOR_DB_TABLE_NAME = "documents"

# ============================================================================
# File Paths Configuration
# ============================================================================

# Documents and data files
DOCUMENTS_CSV_PATH = "app/pages/files/CampaignGenieDocuments - Documents.csv"
TASKS_DIR_PATH = "app/pages/files/tasks"

# ============================================================================
# API Configuration
# ============================================================================

# OpenAI API settings
OPENAI_BASE_URL = "https://api.metisai.ir/openai/v1"
OPENAI_API_KEY_ENV = "METIS_API_KEY"

# Model configurations
MINI_GPT_MODEL_ID = "gpt-4.1-mini"
GPT_MODEL_ID = "gpt-4.1"
EMBEDDING_MODEL_ID = "text-embedding-3-large"

# ============================================================================
# Agent Configuration
# ============================================================================

# Agent storage table names
FIRST_AGENT_TABLE_NAME = "first_agent"
CAMPAIGN_PLANNER_TABLE_NAME = "campaign_planner"
KBGK_AGENT_TABLE_NAME = "kbgk_agent"
CRAWLER_AGENT_TABLE_NAME = "crawler_agent"
AGENT_DEBUG_MODE = True


# ============================================================================
# Helper Functions
# ============================================================================

def get_openai_api_key() -> str:
    """Get the OpenAI API key from environment variables."""
    return os.environ[OPENAI_API_KEY_ENV]

def get_db_connection_path() -> pathlib.Path:
    """Get the main database connection path."""
    return DB_PATH

def get_documents_csv_path() -> str:
    """Get the path to the documents CSV file."""
    return DOCUMENTS_CSV_PATH

def get_vector_db_uri() -> str:
    """Get the vector database URI."""
    return VECTOR_DB_URI

def get_tasks_dir_path() -> str:
    """Get the tasks directory path."""
    return TASKS_DIR_PATH

def get_first_agent_db_path() -> str:
    """Get the first agent database path."""
    return FIRST_AGENT_DB_PATH

def get_campaign_planner_db_path() -> str:
    """Get the campaign planner database path."""
    return CAMPAIGN_PLANNER_DB_PATH

def get_kbgk_agent_db_path() -> str:
    """Get the KBGK agent database path."""
    return KBGK_AGENT_DB_PATH
