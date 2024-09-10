# app/services/query_analyzer_service.py

import logging
logger = logging.getLogger(__name__)

from langchain.prompts import ChatPromptTemplate
from app.config import Config
from app.utils.json_utils import process_node_output
from app.utils.llm_utils import get_llm
from app.models import AnalyzedQuery, AgentState
import json
import logging
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


def query_analyzer_table_selector(state: AgentState) -> AgentState:
    print ("================ Analyzing user query ==================")
    logger.info("Entering query analyzer")
    logger.info(f"Original user query: {state['user_query']}")

    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    relevant_memories = "\n".join([f"Memory {i+1}: {memory.page_content}" for i, memory in enumerate(state.get('relevant_memories', []))])

    prompt = ChatPromptTemplate.from_template("""
            Given the user query: "{user_query}"
            And the following database tables:
            {table_information}

            Consider these relevant memories from past interactions:
            {relevant_memories}

            Task 1: Analyze the user query and determine if it's relevant to the provided database tables.
            Task 2: If relevant, rephrase the query to clarify the data requirements, considering past interactions if applicable.
            Task 3: If relevant, select up to {max_tables} most relevant tables for this query.
            Task 4: Provide a brief explanation of your analysis and selection.

            Important: The query is considered relevant if it can be answered using the available tables, even if it requires joining multiple tables or performing aggregations.

            Respond in the following string JSON format:
            {{
                "is_query_relevant": True/False,
                "analyzed_query": "Rephrased and clarified query (if relevant)",
                "selected_tables": ["table1", "table2", ...] (if relevant),
                "explanation": "Explanation of the analysis and relevance/table selection"
            }}
            Ensure that all selected tables exist in the provided table information.
        """)

    chain = prompt | llm

    try:
        response = chain.invoke({
            "user_query": state["user_query"],
            "table_information": json.dumps({name: info.table_schema.dict() for name, info in state["db_info"].items()},
                                            indent=2),
            "max_tables": Config.MAX_TABLES_TO_SELECT,
            "relevant_memories": relevant_memories
        })

        logger.info(f"Raw LLM response: {response.content}")

        parsed_response = process_node_output(response.content, "analyzer")

        logger.info(f"Parsed response from LLM: {parsed_response}")

        if not parsed_response:
            raise ValueError("Failed to parse LLM response")

        state["analyzed_query"] = AnalyzedQuery(
            original_query=state["user_query"],
            analyzed_query=parsed_response.get('analyzed_query', ''),
            selected_tables=parsed_response.get('selected_tables', []),
            explanation=parsed_response.get('explanation', ''),
            is_query_relevant=parsed_response.get('is_query_relevant', False)
        )
        state["is_query_relevant"] = state["analyzed_query"].is_query_relevant

        logger.info(f"Query relevance set to: {state["is_query_relevant"]}")
        logger.info(f"Analyzed query: {state['analyzed_query'].analyzed_query}")
        logger.info(f"Selected tables: {state['analyzed_query'].selected_tables}")
        logger.info(f"Explanation: {state['analyzed_query'].explanation}")

    except Exception as e:
        logger.error(f"Error in query analyzer: {str(e)}")
        state["analyzed_query"] = AnalyzedQuery(
            original_query=state["user_query"],
            analyzed_query="",
            selected_tables=[],
            explanation=f"An error occurred during analysis: {str(e)}",
            is_query_relevant=False
        )
        state["is_query_relevant"] = False

    logger.info(f"Final query relevance: {state['is_query_relevant']}")

    return state
