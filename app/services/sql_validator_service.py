# app/services/sql_validator_service.py


from langchain.prompts import ChatPromptTemplate
from app.models import SQLValidationResult, AgentState
from app.utils.json_utils import process_node_output
import logging
from app.utils.llm_utils import get_llm
import json

logger = logging.getLogger(__name__)

def sql_validator(state: AgentState) -> AgentState:
    print("============== Validating SQL Code ================")

    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    prompt = ChatPromptTemplate.from_template("""
        Given the following:
        1. Original user query: {original_query}
        2. Analyzed query: {analyzed_query}
        3. Generated SQL query: {sql_query}
        4. SQL query explanation: {sql_explanation}
        5. Selected tables and their schemas:
        {table_schemas}

        Task 1: Validate the SQL query for correctness, safety, and relevance to the original query.
        Task 2: Provide your suggestions to improve the Generated SQL query If the generated SQL query is not Valid.

        Please check for the following:
        1. SQL syntax errors
        2. Potential SQL injection vulnerabilities
        3. Use of non-existent tables or columns
        4. Logical errors in JOIN conditions or WHERE clauses
        5. Appropriate use of aggregation functions and GROUP BY clauses
        6. Relevance of the query to the original user question
        7. Potential performance issues (e.g., missing indexes, inefficient JOINs) 
        8. Avoid Selecting Entire Tables or Columns Without Limits.

        Respond in the following JSON format:
        {{
            "is_sql_valid": True/False,
            "issues": ["issue1", "issue2", ...],
            "suggested_fix": "Suggested SQL query fix or improvements"
        }}

        If the sql query is valid and safe, set is_sql_valid to True and leave issues and suggested_fix empty.
        If issues are found, set is_sql_valid to False, list the issues, and provide a suggested fix.
    """)

    selected_table_schemas = {
        name: state["db_info"][name].table_schema.dict()
        for name in state["analyzed_query"].selected_tables
    }

    chain = prompt | llm

    try:
        response = chain.invoke({
            "original_query": state["analyzed_query"].original_query,
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "sql_query": state["generated_sql"].sql_query,
            "sql_explanation": state["generated_sql"].explanation,
            "table_schemas": json.dumps(selected_table_schemas, indent=2)
        })

        validation_result = process_node_output(response.content, "sql_validator")

        is_sql_valid = validation_result.get('is_sql_valid')
        if is_sql_valid is None:
            logger.warning("Validation result did not contain 'is_valid' field. Assuming SQL is invalid.")
            is_sql_valid = False

        state["validation_result"] = SQLValidationResult(
            is_sql_valid=validation_result.get('is_sql_valid'),
            issues=validation_result.get('issues', []),
            suggested_fix=validation_result.get('suggested_fix', '')
        )

        # Add reflection information to the state
        if is_sql_valid:
            state["reflection"] = None
        else:
            state["reflection"] = {
                "type": "sql_validation",
                "issues": validation_result.get('issues', []),
                "suggested_fix": validation_result.get('suggested_fix', '')
            }

    except Exception as e:
        logger.error(f"Error in SQL validation: {str(e)}")
        state["validation_result"] = SQLValidationResult(
            is_sql_valid=False,
            issues=["Unexpected error in validation process"],
            suggested_fix="Please review the SQL query and try again."
        )
        state["reflection"] = {
            "type": "sql_validation",
            "issues": ["Unexpected error in validation process"],
            "suggested_fix": "Please review the SQL query and try again."
        }

    return state