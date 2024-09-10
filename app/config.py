# app/config.py
import os
from dotenv import load_dotenv
from cachelib import FileSystemCache

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Vector store selection
    USE_CHROMADB = os.getenv('USE_CHROMADB', 'True').lower() == 'true'
    USE_MILVUS = os.getenv('USE_MILVUS', 'False').lower() == 'true'

    # Embedding selection
    USE_OLLAMA = os.getenv('USE_OLLAMA', 'True').lower() == 'true'
    USE_OPENAI = os.getenv('USE_OPENAI', 'False').lower() == 'true'

    # ChromaDB configurations
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'sql_agent_memory')
    CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')


    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'sql_agent_sessions.db')}")

    # Ollama configurations
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')

    # Milvus configurations

    MILVUS_HOST = os.getenv('MILVUS_HOST', 'localhost')
    MILVUS_PORT = os.getenv('MILVUS_PORT', '19530')
    MILVUS_COLLECTION = os.getenv('MILVUS_COLLECTION', 'sql_agent_memory')

    # Session configurations
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR', os.path.join(BASE_DIR, 'flask_session'))
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_CACHELIB = FileSystemCache(SESSION_FILE_DIR)

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ecommerce.db')


    # LLM Settings
    # OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')  # Default Ollama model
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')  # This can serve as a fallback model if needed
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))

    # Application Settings
    MAX_TABLES_TO_SELECT = int(os.getenv('MAX_TABLES_TO_SELECT', '5'))
    MAX_SQL_REFINEMENT_ATTEMPTS = int(os.getenv('MAX_SQL_REFINEMENT_ATTEMPTS', '3'))

    # LangChain and LangSmith Settings
    LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    LANGSMITH_API_KEY = os.getenv('LANGSMITH_API_KEY')

    # Graph Settings
    GRAPH_RECURSION_LIMIT = int(os.getenv('GRAPH_RECURSION_LIMIT', '20'))

