# app/services/memory_service.py
# app/services/memory_service.py
from langchain_milvus import Milvus
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.embedding_function = self._create_embedding_function()
        self.vector_store = self._create_vector_store()
        self.memory_buffer = []
        self.buffer_size = 10

    def initialize(self):
        self.vector_store = self._create_vector_store()
        # Load existing memories or perform any other initialization
        logger.info("MemoryService initialized")

    def _create_embedding_function(self):
        if Config.USE_OLLAMA:
            logger.info("Using Ollama embeddings")
            return OllamaEmbeddings(
                base_url=Config.OLLAMA_BASE_URL,
                model=Config.OLLAMA_MODEL
            )
        elif Config.USE_OPENAI:
            logger.info("Using OpenAI embeddings")
            return OpenAIEmbeddings()
        else:
            logger.error("No valid embedding configuration found")
            raise ValueError("No valid embedding configuration found")

    def _create_vector_store(self):
        if Config.USE_CHROMADB:
            logger.info("Initializing ChromaDB")
            return Chroma(
                collection_name=Config.CHROMA_COLLECTION_NAME,
                embedding_function=self.embedding_function,
                persist_directory=Config.CHROMA_PERSIST_DIRECTORY
            )
        elif Config.USE_MILVUS:
            logger.info("Initializing Milvus")
            from langchain_community.vectorstores import Milvus
            return Milvus(
                embedding_function=self.embedding_function,
                collection_name=Config.MILVUS_COLLECTION,
                connection_args={"host": Config.MILVUS_HOST, "port": Config.MILVUS_PORT}
            )
        else:
            logger.error("No valid vector store configuration found")
            raise ValueError("No valid vector store configuration found")

    def add_memory(self, text, metadata=None):
        try:
            self.vector_store.add_texts([text], metadatas=[metadata] if metadata else None)
            if isinstance(self.vector_store, Chroma):
                self.vector_store.persist()  # Only for ChromaDB
            logger.info(f"Successfully added memory: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to add memory: {str(e)}")
            raise

    def search_memory(self, query, k=5):
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Successfully searched memory for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Failed to search memory: {str(e)}")
            return []

    def clear_memory(self):
        try:
            if isinstance(self.vector_store, Chroma):
                self.vector_store.delete_collection()
                self.vector_store = self._create_vector_store()
            elif isinstance(self.vector_store, Milvus):
                self.vector_store.drop()
                self.vector_store = self._create_vector_store()
            logger.info("Successfully cleared memory")
        except Exception as e:
            logger.error(f"Failed to clear memory: {str(e)}")
            raise