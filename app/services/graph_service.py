# app/services/graph_service.py
from app.services.visualizer_service import data_visualizer, visualization_check

import os
import requests
import logging
import time
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.runnables.graph import MermaidDrawMethod
from app.models import AgentState, EvaluationResult
from app.services.database_service import DatabaseService
from app.services.query_analyzer_service import query_analyzer_table_selector
from app.services.sql_generator_service import sql_generator_optimizer, sql_generator_optimizer_reflection
from app.services.sql_executor_service import execute_sql, execute_sql_reflection, execute_sql_corrected
from app.services.result_evaluator_service import result_evaluator
from app.services.visualizer_service import data_visualizer, visualization_check
from app.services.sql_validator_service import sql_validator
from app.services.summarizer_service import summarizer_node
from app.services.sql_reflection_service import sql_reflection
from app.services.sql_correction_service import correct_sql


logger = logging.getLogger(__name__)

def should_reflect_result(state: AgentState) -> str:
    return "visualization_check" if state["is_result_relevant"] else "sql_corrected" # "sql_reflector"

def append_to_list(state: AgentState, list_name: str) -> None:
    try:
        state[list_name].append("attempt")
    except KeyError:
        logger.error(f"List {list_name} not found in state. Creating new list.")
        state[list_name] = ["attempt"]

def should_regenerate_sql(state: AgentState) -> str:
    if (state["validation_result"] is None or not state["validation_result"].is_sql_valid) and \
            len(state.get("regenerate_list", [])) < 3:
        append_to_list(state, "regenerate_list")
        logger.info(f"Regenerating SQL. New attempt count: {len(state['regenerate_list'])}")
        return "generator"
    elif len(state.get("regenerate_list", [])) >= 3:
        logger.info("Max SQL regeneration attempts reached. Moving to executor.")
        state["reflection"] = None
        return "executor"
    else:
        logger.info("SQL is valid. Moving to executor.")
        state["reflection"] = None
        return "executor"

def is_query_relevant(state: AgentState) -> str:
    return "generator" if state["is_query_relevant"] else "summarizer"

def should_visualize(state: AgentState) -> str:
    evaluation_result = state.get("evaluation_result")
    if evaluation_result and isinstance(evaluation_result, EvaluationResult) and evaluation_result.requires_visualization:
        return "visualizer"
    return "summarizer"

def create_analysis_graph(memory_service) -> StateGraph:
    graph = StateGraph(AgentState)

    # Define the graph nodes
    graph.add_node("db_information", DatabaseService.get_database_info)
    graph.add_node("analyzer", query_analyzer_table_selector)
    graph.add_node("generator", sql_generator_optimizer)
    graph.add_node("validator", sql_validator)
    graph.add_node("executor", execute_sql)
    graph.add_node("evaluator", result_evaluator)
    graph.add_node("visualization_check", visualization_check)
    graph.add_node("visualizer", data_visualizer)
    graph.add_node("summarizer", summarizer_node)

    # # Removing add memory node
    # graph.add_node("add_to_memory", lambda state: memory_service.add_memory(
    #     text=f"Query: {state['user_query']}\nResponse: {state['summary']}",
    #     metadata={"session_id": state['session_id']}
    # ))
    # Reflection branch
    graph.add_node("sql_corrected", correct_sql)
    graph.add_node("executor_corrected", execute_sql_corrected)

    # TODO: Add reflection nodes
    # graph.add_node("sql_reflector", sql_reflection)
    # graph.add_node("generator_reflection", sql_generator_optimizer_reflection)
    # graph.add_node("executor_reflection", execute_sql_reflection)

    # Build the graph with conditional edges
    graph.set_entry_point("db_information")
    graph.add_edge("db_information", "analyzer")

    graph.add_conditional_edges(
        "analyzer",
        is_query_relevant,
        {
            "generator": "generator",
            "summarizer": "summarizer"
        }
    )
    graph.add_edge("generator", "validator")

    graph.add_conditional_edges(
        "validator",
        should_regenerate_sql,
        {
            "generator": "generator",
            "executor": "executor"
        }
    )

    # Result Evaluation Reflection Loop
    graph.add_edge("executor", "evaluator")
    graph.add_conditional_edges(
        "evaluator",
        should_reflect_result,
        {
            #TODO: Add reflection nodes
            #"sql_reflector": "sql_reflector",
            "sql_corrected": "sql_corrected",
            "visualization_check": "visualization_check"
        }
    )

    # TODO: Add reflection nodes
    # graph.add_edge("sql_reflector", "generator_reflection")
    # graph.add_edge("generator_reflection", "executor_reflection")

    graph.add_edge("sql_corrected", "executor_corrected")
    graph.add_edge("executor_corrected", "visualization_check")

    graph.add_conditional_edges(
        "visualization_check",
        should_visualize,
        {
            "visualizer": "visualizer",
            "summarizer": "summarizer",
        }
    )

    graph.add_edge("visualizer", "summarizer")
    graph.add_edge("summarizer", END)

    # removing add_memory node (adding data to memory will be done outside the graph)
    #graph.add_edge("add_to_memory", END)

    #save_graph_visualization(graph)

    compiled_graph = graph.compile()

    return compiled_graph

def save_graph_visualization(graph: StateGraph):
    try:
        start_time = time.time()
        logger.info("Starting graph visualization")

        mermaid_string = graph.get_graph().draw_mermaid()

        logger.info("Sending request to mermaid.ink API")
        response = requests.post(
            "https://mermaid.ink/img",
            json={"mermaid": mermaid_string}
        )
        response.raise_for_status()
        png_content = response.content

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        file_path = os.path.join(project_dir, 'analysis_graph.png')

        with open(file_path, 'wb') as f:
            f.write(png_content)

        end_time = time.time()
        logger.info(f"Graph visualization saved to {file_path}")
        logger.info(f"Graph visualization completed in {end_time - start_time:.2f} seconds")

        print(f"Graph visualization saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving graph visualization: {str(e)}", exc_info=True)