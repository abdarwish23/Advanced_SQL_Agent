# app/routes.py
import json
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from app.services.graph_service import create_analysis_graph
from app.config import Config
from app.services.session_service import SessionService
from app import memory_service
from app.models import AgentState
import traceback
import logging
import time
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context, render_template

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/analyze', methods=['POST'])
def analyze_query():
    start_time = time.time()
    logger.info("Starting query analysis")

    data = request.json
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Session setup
        session_id = SessionService.get_or_create_session()
        run_id = SessionService.create_run()

        # Memory search
        relevant_memories = memory_service.search_memory(user_query)

        # Create analysis graph
        analysis_graph = create_analysis_graph(memory_service)

        # Prepare initial state
        initial_state = AgentState(
            user_query=user_query,
            db_info=None,
            analyzed_query=None,
            generated_sql=None,
            validation_result=None,
            execution_result=None,
            evaluation_result=None,
            visualization=None,
            summary=None,
            error=None,
            is_query_relevant=False,
            is_result_relevant=False,
            regenerate_list=[],
            reanalyze_list=[],
            reflection=None,
            reflected_generated_sql=None,
            relevant_memories=relevant_memories,
            session_id=session_id,
            run_id=run_id,
            recent_history=[],
            sql_correction=None
        )

        # Invoke graph
        final_state = analysis_graph.invoke(initial_state)

        # Prepare response
        response = {
            "summary": final_state.get('summary', "No summary available."),
            "visualization": None
        }

        if final_state.get('visualization'):
            response["visualization"] = {
                "image": final_state['visualization'].image,
                "description": final_state['visualization'].description
            }

        # Add interaction to long-term memory
        memory_service.add_memory(
            text=f"Query: {user_query}\nResponse: {response['summary']}",
            metadata={"session_id": session_id, "run_id": run_id}
        )

        # Add interaction to session history
        SessionService.add_to_session_history(
            session_id=session_id,
            run_id=run_id,
            query=user_query,
            response=response['summary']
        )

        end_time = time.time()
        logger.info(f"Total query analysis completed in {end_time - start_time:.2f} seconds")

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in analyze_query: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@main_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    try:
        # Session setup
        session_id = SessionService.get_or_create_session()
        run_id = SessionService.create_run()

        # Memory search
        relevant_memories = memory_service.search_memory(user_query)

        # Create analysis graph
        analysis_graph = create_analysis_graph(memory_service)

        # Prepare initial state
        initial_state = AgentState(
            user_query=user_query,
            db_info=None,
            analyzed_query=None,
            generated_sql=None,
            validation_result=None,
            execution_result=None,
            evaluation_result=None,
            visualization=None,
            summary=None,
            error=None,
            is_query_relevant=False,
            is_result_relevant=False,
            regenerate_list=[],
            reanalyze_list=[],
            reflection=None,
            reflected_generated_sql=None,
            relevant_memories=relevant_memories,
            session_id=session_id,
            run_id=run_id,
            recent_history=[],
            sql_correction=None
        )

        final_state = analysis_graph.invoke(initial_state)

        if final_state:
            response = {
                "summary": final_state.get('summary', "No summary available."),
                "visualization": None
            }

            if final_state.get('visualization'):
                response["visualization"] = {
                    "image": final_state['visualization'].image,
                    "description": final_state['visualization'].description
                }

            # Add interaction to long-term memory
            memory_service.add_memory(
                text=f"Query: {user_query}\nResponse: {response['summary']}",
                metadata={"session_id": session_id, "run_id": run_id}
            )

            # Add interaction to session history
            SessionService.add_to_session_history(
                session_id=session_id,
                run_id=run_id,
                query=user_query,
                response=response['summary']
            )

            return jsonify(response)

        else:
            return jsonify({"error": "No result generated"}), 500

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    

@main_bp.route('/stream', methods=['POST'])
def stream_chat():
    data = request.json
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    def generate():
        try:
            # Session setup
            session_id = SessionService.get_or_create_session()
            run_id = SessionService.create_run()

            # Memory search
            relevant_memories = memory_service.search_memory(user_query)

            # Create analysis graph
            analysis_graph = create_analysis_graph(memory_service)

            # Prepare initial state
            initial_state = AgentState(
                user_query=user_query,
                db_info=None,
                analyzed_query=None,
                generated_sql=None,
                validation_result=None,
                execution_result=None,
                evaluation_result=None,
                visualization=None,
                summary=None,
                error=None,
                is_query_relevant=False,
                is_result_relevant=False,
                regenerate_list=[],
                reanalyze_list=[],
                reflection=None,
                reflected_generated_sql=None,
                relevant_memories=relevant_memories,
                session_id=session_id,
                run_id=run_id,
                recent_history=[],
                sql_correction=None
            )

            for state in analysis_graph.stream(initial_state):
                # Stream intermediate results
                yield json.dumps({"type": "update", "content": str(state)}) + "\n"

            # Final result
            response = {
                "summary": state.get('summary', "No summary available."),
                "visualization": None
            }

            if state.get('visualization'):
                response["visualization"] = {
                    "image": state['visualization'].image,
                    "description": state['visualization'].description
                }

            # Add interaction to long-term memory
            memory_service.add_memory(
                text=f"Query: {user_query}\nResponse: {response['summary']}",
                metadata={"session_id": session_id, "run_id": run_id}
            )

            # Add interaction to session history
            SessionService.add_to_session_history(
                session_id=session_id,
                run_id=run_id,
                query=user_query,
                response=response['summary']
            )

            yield json.dumps({"type": "final", "content": response}) + "\n"

        except Exception as e:
            logger.error(f"Error in stream_chat: {str(e)}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return Response(stream_with_context(generate()), content_type='application/json')