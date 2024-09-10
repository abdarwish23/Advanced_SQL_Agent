# app/services/sql_executor_service.py

from sqlalchemy import create_engine, text
from app.config import Config
from app.models import SQLExecutionResult, SQLCorrectionResult
import pandas as pd
from app.models import AgentState



def execute_sql(state: AgentState) -> AgentState:
    print ("============= Executing SQL Code ==============")
    engine = create_engine(Config.DATABASE_URL)
    try:
        with engine.connect() as connection:
            result = connection.execute(text(state["generated_sql"].sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        state["execution_result"] = SQLExecutionResult(success=True, data=df.to_dict(orient='records'))
    except Exception as e:
        state["execution_result"] = SQLExecutionResult(success=False, error_message=str(e))
    return state



def execute_sql_reflection(state: AgentState) -> AgentState:
    print ("============= [Reflection] Executing SQL Code ==============")
    engine = create_engine(Config.DATABASE_URL)
    try:
        with engine.connect() as connection:
            result = connection.execute(text(state["reflected_generated_sql"].reflected_sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        state["execution_result"] = SQLExecutionResult(success=True, data=df.to_dict(orient='records'))
    except Exception as e:
        state["execution_result"] = SQLExecutionResult(success=False, error_message=str(e))
    return state



def execute_sql_corrected(state: AgentState) -> AgentState:
    print ("============= [Correction] Executing SQL Code ==============")
    engine = create_engine(Config.DATABASE_URL)
    try:
        with engine.connect() as connection:
            result = connection.execute(text(state["sql_correction"].corrected_sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        state["execution_result"] = SQLExecutionResult(success=True, data=df.to_dict(orient='records'))
    except Exception as e:
        state["execution_result"] = SQLExecutionResult(success=False, error_message=str(e))
    return state