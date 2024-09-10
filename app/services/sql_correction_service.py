# app/services/sql_correction_service.py
from langchain.prompts import ChatPromptTemplate
from app.models import AgentState, SQLCorrectionResult
from app.utils.llm_utils import get_llm
from app.utils.json_utils import process_node_output
import logging
import json

logger = logging.getLogger(__name__)



def correct_sql(state: AgentState) -> AgentState:
    print("================== SQL Correction =================")
    logger.info("Entering SQL correction")

    llm = get_llm("openai", "gpt-3.5-turbo")  # You can adjust the model as needed

    prompt = ChatPromptTemplate.from_template("""
        Given the following information:
        1. Original user query: {original_query}
        2. Analyzed query: {analyzed_query}
        3. Current SQL query: {current_sql}
        4. Evaluation result: {evaluation_result}
        5. Database schema: {table_information}

        Task: Analyze why the current SQL query does not produce results relevant to the user's query. 
        Then, provide a corrected SQL query that addresses the issues and is more likely to produce relevant results.

        Consider the following:
        - Are there any misinterpretations of the user's intent?
        - Are there missing JOINs, WHERE clauses, or aggregations?
        - Is the query structure appropriate for the user's question?
        - Are there any syntax errors or logical flaws in the current SQL?

        Respond in the following JSON format:
        {{
            "analysis": "Your analysis of why the current SQL query is not producing relevant results",
            "identified_issues": "List of specific issues identified in the current SQL query",
            "corrected_sql_query": "A corrected SQL query that addresses the identified issues"
        }}
    """)

    chain = prompt | llm

    try:
        response = chain.invoke({
            "original_query": state["analyzed_query"].original_query,
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "current_sql": state["generated_sql"].sql_query if state["generated_sql"] else "",
            "evaluation_result": state["evaluation_result"].dict() if state["evaluation_result"] else None,
            "table_information": json.dumps({name: info.table_schema.dict() for name, info in state["db_info"].items()}, indent=2),
        })

        parsed_response = process_node_output(response.content, "sql_correction")

        state["sql_correction"] = SQLCorrectionResult(
            analysis=parsed_response.get("analysis", "No analysis provided"),
            identified_issues=parsed_response.get("identified_issues", "No issues identified"),
            corrected_sql_query=parsed_response.get("corrected_sql_query", state["generated_sql"].sql_query if state["generated_sql"] else "")
        )

    except Exception as e:
        logger.error(f"Error in SQL correction: {str(e)}")
        state["sql_correction"] = {
            "error": f"An error occurred during SQL correction: {str(e)}",
            "corrected_sql_query": state["generated_sql"].sql_query if state["generated_sql"] else ""
        }

    return state

