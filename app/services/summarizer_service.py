# app/services/summarizer_service.py

from langchain.prompts import ChatPromptTemplate
from app.models import AgentState
import json
from app.utils.llm_utils import get_llm

def summarizer_node(state: AgentState) -> AgentState:
    print("=================== Summarization =====================")
    if not state["analyzed_query"].is_query_relevant:
        state['summary'] = f"I'm sorry, but your query '{state['user_query']}' is not relevant to the available database information. {state['analyzed_query'].explanation}"
        return state

    #llm = ChatOpenAI(model_name=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE)
    llm = get_llm("openai","gpt-3.5-turbo") # gpt-3.5-turbo, GPT-4o-mini
    # llm = get_llm("groq", "gemma2-9b-it") # llama-3.1-70b-versatile, llama3-groq-70b-8192-tool-use-preview, gemma2-9b-it, mixtral-8x7b-32768, llama-3.1-8b-instant

    prompt = ChatPromptTemplate.from_template("""
        Given the following information:
        1. Original user query: {user_query}
        2. Analyzed query: {analyzed_query}
        3. SQL query executed: {sql_query}
        4. Query execution result: {execution_result}
        5. Result evaluation: {evaluation_result}

        Please provide an insightful answer to the user's original query. 
        Your response should be clear, concise, and directly address the user's question 
        while incorporating the relevant information from the query results.

        Answer:
    """)

    chain = prompt | llm | (lambda x: x.content)

    response = chain.invoke({
        "user_query": state['user_query'],
        "analyzed_query": state['analyzed_query'].analyzed_query,
        "sql_query": state['generated_sql'].sql_query if state['generated_sql'] else "",
        "execution_result": json.dumps(state['execution_result'].data) if state['execution_result'] else "",
        "evaluation_result": state['evaluation_result'].explanation if state['evaluation_result'] else ""
    })

    state['summary'] = response
    return state