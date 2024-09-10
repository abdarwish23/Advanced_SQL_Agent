# tests/test_api.py

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from app import create_app
from app.config import Config
from app.services.memory_service import MemoryService

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = tempfile.mkdtemp()
    CHROMA_PERSIST_DIRECTORY = tempfile.mkdtemp()
    USE_CHROMADB = True
    USE_MILVUS = False
    USE_OLLAMA = True
    USE_OPENAI = False

class TestAPI(unittest.TestCase):
    @patch('app.services.memory_service.Chroma')
    @patch('app.services.memory_service.OllamaEmbeddings')
    @patch('app.services.memory_service.OpenAIEmbeddings')
    @patch('app.services.session_service.SessionService')
    def setUp(self, mock_session_service, mock_openai, mock_ollama, mock_chroma):
        # Mock ChromaDB
        self.mock_vector_store = MagicMock()
        mock_chroma.return_value = self.mock_vector_store

        # Mock embeddings
        mock_ollama.return_value = MagicMock()
        mock_openai.return_value = MagicMock()

        # Mock SessionService
        self.mock_session_service = mock_session_service
        self.mock_session_service.get_or_create_session.return_value = 'test-session-id'
        self.mock_session_service.create_run.return_value = 'test-run-id'
        self.mock_session_service.get_recent_history.return_value = []

        # Create app with test config
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Initialize the database
        from app.models import db
        db.create_all()

    def tearDown(self):
        # Clean up the database
        from app.models import db
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

        # Clean up the temporary directories
        shutil.rmtree(TestConfig.SESSION_FILE_DIR, ignore_errors=True)
        shutil.rmtree(TestConfig.CHROMA_PERSIST_DIRECTORY, ignore_errors=True)

    @patch('app.routes.create_analysis_graph')
    def test_analyze_query_endpoint(self, mock_create_analysis_graph):
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "user_query": "Test query",
            "summary": "Test summary"
        }
        mock_create_analysis_graph.return_value = mock_graph

        response = self.client.post('/analyze', json={"query": "What are the top 5 customers by total order amount?"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('user_query', data)
        self.assertIn('summary', data)

    def test_analyze_query_no_input(self):
        response = self.client.post('/analyze', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()