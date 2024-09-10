# app/services/result_evaluator_service.py

import pandas as pd
from app.utils.json_utils import process_node_output
from langchain.prompts import ChatPromptTemplate
from app.models import EvaluationResult, AgentState
import logging
from app.utils.llm_utils import get_llm
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

def result_evaluator(state: AgentState) -> AgentState:
    print("================= Evaluating the results =================")
    logger.info("Entering result evaluator")

    if not state["execution_result"].success:
        state["evaluation_result"] = EvaluationResult(
            is_result_relevant=False,
            explanation=f"Query execution failed: {state['execution_result'].error_message}",
            requires_visualization=False,
            summary="The query execution failed, so no results are available to summarize."
        )
        state["is_result_relevant"] = False
        state["reflection"] = {
            "type": "result_evaluation",
            "issue": "Query execution failed",
            "suggestion": "Review and fix the SQL query execution error"
        }
        return state

    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it")  # gpt-3.5-turbo, GPT-4o-mini

    df = pd.DataFrame(state["execution_result"].data)
    results_summary = df.describe().to_string() if not df.empty else "No results"

    # Ensure session_id is available in the state
    session_id = state.get("session_id")
    if not session_id:
        logger.warning("Session ID not found in state")
        session_history_summary = "No session history available"
    else:
        try:
            session_history = SessionService.get_session_history(session_id=session_id)
            session_history_summary = "\n".join([f"Query: {item.query}\nResponse: {item.response}" for item in session_history])
        except Exception as e:
            logger.error(f"Error fetching session history: {str(e)}", exc_info=True)
            session_history_summary = "Error fetching session history"

    prompt = ChatPromptTemplate.from_template("""
        Given the following:
        1. Original user query: {original_query}
        2. Analyzed query: {analyzed_query}
        3. Generated SQL query: {generated_sql}
        4. Query results summary:
        {results_summary}
        5. Session history:
        {session_history}

        Task 1: Evaluate the relevance and quality of the query results to the original user query.
        Task 2: If not relevant, provide explanation and suggestions on how to improve the SQL query to better answer the original user query.
        Task 3: Act as a data analysis expert to determine whether the results require visualization. Consider the following:
           - Simple questions requiring single answers (e.g., percentages, counts, totals) do not need visualization.
           - Examples of queries not requiring visualization include:
             * What is the percentage of successful orders?
             * How many orders do we have?
             * How many customers are there?
             * What is the total number of orders?
           - More complex queries or those involving comparisons or trends typically benefit from visualization.
        Task 4: Summarize the findings in a concise, user-friendly manner.

        Respond in the following JSON format:
        {{
            "is_result_relevant": True/False,
            "explanation": "Detailed explanation of your evaluation",
            "improvement_suggestion": "Suggestion on how to improve the SQL query if not relevant",
            "requires_visualization": True/False,
            "summary": "Your human-friendly summary here"
        }}
    """)

    chain = prompt | llm

    try:
        response = chain.invoke({
            "original_query": state["analyzed_query"].original_query,
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "generated_sql": state["generated_sql"].sql_query,
            "results_summary": results_summary,
            "session_history": session_history_summary
        })

        parsed_response = process_node_output(response.content, "result_evaluator")

        state["evaluation_result"] = EvaluationResult(
            is_result_relevant=parsed_response.get('is_result_relevant', False),
            explanation=parsed_response.get('explanation', "Failed to generate explanation"),
            requires_visualization=parsed_response.get('requires_visualization', False),
            summary=parsed_response.get('summary', "Failed to generate summary")
        )
        state["is_result_relevant"] = state["evaluation_result"].is_result_relevant

        if not state["is_result_relevant"]:
            state["reflection"] = {
                "type": "result_evaluation",
                "issue": "Results not relevant to user query",
                "suggestion": parsed_response.get('improvement_suggestion', "No suggestion provided")
            }
        else:
            state["reflection"] = None

    except Exception as e:
        logger.error(f"Error in result evaluator: {str(e)}", exc_info=True)
        state["evaluation_result"] = EvaluationResult(
            is_result_relevant=False,
            explanation=f"An error occurred during evaluation: {str(e)}",
            requires_visualization=False,
            summary="Failed to evaluate results due to an error."
        )
        state["is_result_relevant"] = False
        state["reflection"] = {
            "type": "result_evaluation",
            "issue": "Error during evaluation",
            "suggestion": "Review and fix the evaluation process"
        }

    logger.info(f"Result relevance: {state['is_result_relevant']}")
    logger.info(f"Requires visualization: {state['evaluation_result'].requires_visualization}")

    return state

