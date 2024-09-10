
# app/services/sql_reflection_service.py
from langchain.prompts import ChatPromptTemplate
from app.models import AgentState
from app.utils.llm_utils import get_llm
from app.utils.json_utils import process_node_output
import logging

logger = logging.getLogger(__name__)

def sql_reflection(state: AgentState) -> AgentState:
    print ("================== SQL Reflection =================" )
    logger.info("Entering SQL reflection")

    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    prompt = ChatPromptTemplate.from_template("""
        Given the following information:
        1. Original user query: {original_query}
        2. Analyzed query: {analyzed_query}
        3. Current SQL query: {current_sql}
        4. Evaluation result: {evaluation_result}
        5. Reflection: {reflection}

        Task: Analyze the current SQL query and suggest improvements to make it more relevant to the original user query.

        Respond in the following JSON format:
        {{
            "analysis": "Your analysis of the current SQL query",
            "suggested_improvements": "Detailed suggestions for improving the SQL query",
            "revised_sql_query": "A revised SQL query based on your suggestions"
        }}
    """)

    chain = prompt | llm

    try:
        response = chain.invoke({
            "original_query": state["analyzed_query"].original_query,
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "current_sql": state["generated_sql"].sql_query if state["generated_sql"] else "",
            "evaluation_result": state["evaluation_result"].dict() if state["evaluation_result"] else None,
            "reflection": state["reflection"]
        })

        parsed_response = process_node_output(response.content, "sql_reflection")

        state["reflection"] = {
            "type": "sql_reflection",
            "analysis": parsed_response.get("analysis", "No analysis provided"),
            "suggested_improvements": parsed_response.get("suggested_improvements", "No improvements suggested"),
            "revised_sql_query": parsed_response.get("revised_sql_query", state["generated_sql"].sql_query if state["generated_sql"] else "")
        }


    except Exception as e:
        logger.error(f"Error in SQL reflection: {str(e)}")
        state["reflection"] = {
            "type": "sql_reflection",
            "error": f"An error occurred during SQL reflection: {str(e)}",
            "suggested_improvements": "Unable to suggest improvements due to an error",
            "revised_sql_query": state["generated_sql"].sql_query if state["generated_sql"] else ""
        }
    return state