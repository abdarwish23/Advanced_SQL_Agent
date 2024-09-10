# app/services/session_service.py

from flask import session
import uuid
from app.models import db, SessionHistory
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

class SessionService:
    @staticmethod
    def get_or_create_session():
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        return session['user_id']

    @staticmethod
    def create_run():
        return str(uuid.uuid4())

    @staticmethod
    def get_session_history(session_id, limit=10):
        if not session_id:
            logger.warning("get_session_history called without session_id")
            return []
        try:
            return db.session.query(SessionHistory).filter(SessionHistory.session_id == session_id)\
                .order_by(desc(SessionHistory.timestamp))\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error(f"Error in get_session_history: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def add_to_session_history(session_id, run_id, query, response):
        if not session_id:
            logger.warning("add_to_session_history called without session_id")
            return
        try:
            new_history = SessionHistory(
                session_id=session_id,
                run_id=run_id,
                query=query,
                response=response
            )
            db.session.add(new_history)
            db.session.commit()
            logger.info(f"Added new history entry for session {session_id}")
        except Exception as e:
            logger.error(f"Error in add_to_session_history: {str(e)}", exc_info=True)
            db.session.rollback()

    @staticmethod
    def get_recent_history(session_id, limit=5):
        if not session_id:
            logger.warning("get_recent_history called without session_id")
            return []
        try:
            recent_history = SessionService.get_session_history(session_id=session_id, limit=limit)
            return [
                {
                    "query": history.query,
                    "response": history.response,
                    "timestamp": history.timestamp.isoformat()
                }
                for history in recent_history
            ]
        except Exception as e:
            logger.error(f"Error in get_recent_history: {str(e)}", exc_info=True)
            return []