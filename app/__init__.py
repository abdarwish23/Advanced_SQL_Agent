# app/__init__.py

import os
import logging
import matplotlib
matplotlib.use('Agg')

from flask import Flask
from flask_session import Session
from flask_cors import CORS  # Add this import
from cachelib import FileSystemCache
from langchain.globals import set_debug, set_verbose

from .config import Config
from .utils.json_encoder import CustomJSONProvider
from .models import db
from .services.memory_service import MemoryService

memory_service = None  # Global variable to hold the MemoryService instance

def create_app(config_class=Config):
    global memory_service
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config_class)
    app.json = CustomJSONProvider(app)

    # Initialize CORS
    CORS(app)  # Add this line to enable CORS for all routes

    # Initialize Flask-Session with FileSystemCache
    app.config['SESSION_CACHELIB'] = FileSystemCache(app.config['SESSION_FILE_DIR'])
    Session(app)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Configure logging
    if not app.debug:
        file_handler = logging.FileHandler('error.log')
        file_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)

    # Initialize MemoryService
    with app.app_context():
        try:
            memory_service = MemoryService()
            memory_service.initialize()  # Load existing memories
            app.memory_service = memory_service
        except Exception as e:
            app.logger.error(f"Failed to initialize MemoryService: {str(e)}")
            app.memory_service = None

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Configure LangChain tracing
    if app.config.get('LANGCHAIN_TRACING_V2'):
        set_debug(True)
        set_verbose(True)
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
        os.environ['LANGSMITH_API_KEY'] = app.config.get('LANGSMITH_API_KEY', '')

    # Create all database tables
    with app.app_context():
        db.create_all()

    return app