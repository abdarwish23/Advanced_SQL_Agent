# app/services/sql_generator_service.py

from langchain.prompts import ChatPromptTemplate
from app.models import GeneratedSQL, ReflectedGeneratedSQL
import json
import logging
from app.models import AgentState
from app.utils.json_utils import process_node_output
from app.utils.llm_utils import get_llm


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sql_generator_optimizer(state: AgentState) -> AgentState:
    print("============== Generate SQL Code ================")

    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    relevant_memories = state.get('relevant_memories', [])
    memories_text = "\n".join([f"Memory {i+1}: {memory.page_content}" for i, memory in enumerate(relevant_memories)])

    prompt = ChatPromptTemplate.from_template("""
        Given the analyzed query: "{analyzed_query}"
        And the following selected table information:
        {table_information}
        
        Consider these relevant memories from past interactions:
        {relevant_memories}
        
        Task 1: Generate an optimized SQL query to answer the analyzed query.
        Task 2: Provide a brief explanation of your query and any optimizations applied.

        Important: 
        - Ensure the generated SQL is valid and complete. Do not use placeholders or omit any necessary parts of the query.
        - Ensure the SQL code does not fetch all tables or databases
        - Ensure there is no any delete or modify commands in the generated SQL code.

        Respond in the following JSON format:
        {{
            "sql_query": "Your complete and valid SQL query",
            "explanation": "Explanation of the query and optimizations"
        }}
        Ensure that the SQL query is valid for the database type being used and uses only the selected tables.
    """)

    selected_table_info = {
        name: info.table_schema.dict() for name, info in state["db_info"].items()
        if name in state["analyzed_query"].selected_tables
    }

    chain = prompt | llm

    try:
        response = chain.invoke({
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "table_information": json.dumps(selected_table_info, indent=2),
            "relevant_memories": memories_text

        })

        # Use the safe_parse_json function to handle both JSON object and string JSON
        parsed_response = process_node_output(response.content, "generator")

        sql_query = parsed_response.get('sql_query', '').replace('\\n', '\n')

        state["generated_sql"] = GeneratedSQL(
            sql_query=sql_query,
            explanation=parsed_response.get('explanation','')
        )
    except Exception as e:
        logger.error(f"Error in sql_generator_optimizer: {str(e)}")
        state["generated_sql"] = GeneratedSQL(
            sql_query="SELECT 'Error: Failed to generate SQL query'",
            explanation=f"An error occurred: {str(e)}"
        )

    logger.info(f"Generated SQL: {state['generated_sql'].sql_query}")
    logger.info(f"Explanation: {state['generated_sql'].explanation}")

    return state


def sql_generator_optimizer_reflection(state: AgentState) -> AgentState:
    print("============== [Reflection] Generate SQL Code ================")
    logger.info("Entering SQL generator optimizer reflection")
    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    prompt = ChatPromptTemplate.from_template("""
        Given the analyzed query: "{analyzed_query}"
        And the following selected table information: {table_information},
        reflection {reflection}.

        Task 1: Consider the suggestion from {reflection} and Generate an optimized SQL query to answer the user query.
        Task 2: Provide a brief explanation of your query and any optimizations applied.

        Important: 
        - Ensure the generated SQL is valid and complete. Do not use placeholders or omit any necessary parts of the query.
        - Ensure the SQL code does not fetch all tables or databases
        - Ensure there is no any delete or modify commands in the generated SQL code.

        Respond in the following JSON format:
        {{
            "reflected_sql_query": "Your complete and valid SQL query",
            "reflected_explanation": "Explanation of the query and optimizations"
        }}
        Ensure that the SQL query is valid for the database type being used and uses only the selected tables.
    """)

    selected_table_info = {
        name: info.table_schema.dict() for name, info in state["db_info"].items()
        if name in state["analyzed_query"].selected_tables
    }

    chain = prompt | llm

    try:
        response = chain.invoke({
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "table_information": json.dumps(selected_table_info, indent=2),
            "reflection": state["reflection"],
        })

        parsed_response = process_node_output(response.content, "generator_reflection")

        state["reflected_generated_sql"] = ReflectedGeneratedSQL(
            reflected_sql_query=parsed_response.get('sql_query', "SELECT 'Error: Failed to generate SQL query'"),
            reflected_explanation=parsed_response.get('explanation', "Failed to generate explanation")
        )
    except Exception as e:
        logger.error(f"Error in sql_generator_optimizer_reflection: {str(e)}")
        state["reflected_generated_sql"] = ReflectedGeneratedSQL(
            reflected_sql_query="SELECT 'Error: Failed to generate SQL query'",
            reflected_explanation=f"An error occurred: {str(e)}"
        )

    logger.info(f"Reflected Generated SQL: {state['reflected_generated_sql'].reflected_sql_query}")
    logger.info(f"Reflected explanation: {state['reflected_generated_sql'].reflected_explanation}")

    return state