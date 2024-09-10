# app/models.py
from typing import TypedDict
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Dict, List, Any, Optional
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SessionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), nullable=False)
    run_id = db.Column(db.String(50), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SessionHistory {self.id}>'

class TableSchema(BaseModel):
    name: str
    columns: Dict[str, str]

class TableSample(BaseModel):
    name: str
    data: List[Dict[str, Any]]

class TableInfo(BaseModel):
    table_schema: TableSchema
    sample: TableSample

class AnalyzedQuery(BaseModel):
    original_query: str
    analyzed_query: str
    selected_tables: List[str]
    explanation: str
    is_query_relevant: bool

class GeneratedSQL(BaseModel):
    sql_query: str
    explanation: str

class ReflectedGeneratedSQL(BaseModel):
    reflected_sql_query: str
    reflected_explanation: str

class SQLValidationResult(BaseModel):
    is_sql_valid: bool = Field(description="Whether the SQL query is valid and safe to execute")
    issues: List[str] = Field(default_factory=list, description="List of identified issues with the SQL query")
    suggested_fix: str = Field(default="", description="Suggested fix for the SQL query if issues are found")

class SQLExecutionResult(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None

class EvaluationResult(BaseModel):
    is_result_relevant: bool = Field(description="Whether the results are relevant to the original query")
    explanation: str = Field(description="Explanation of the evaluation")
    requires_visualization: bool = Field(description="Whether the results would benefit from visualization")
    summary: str = Field(description="Human-friendly summary of the results")

class Visualization(BaseModel):
    image: str = Field(description="Base64 encoded image of the visualization")
    description: str = Field(description="Description of the visualization")


class SQLCorrectionResult(BaseModel):
    analysis: str = Field(default="No analysis provided", description="Analysis of why the current SQL query is not producing relevant results")
    identified_issues: str = Field(default="No issues identified", description="List of specific issues identified in the current SQL query")
    corrected_sql_query: str = Field(default="", description="A corrected SQL query that addresses the identified issues")

class AgentState(TypedDict):
    user_query: str
    db_info: Optional[dict]
    analyzed_query: Optional[AnalyzedQuery]
    generated_sql: Optional[GeneratedSQL]
    validation_result: Optional[SQLValidationResult]
    execution_result: Optional[SQLExecutionResult]
    evaluation_result: Optional[EvaluationResult]
    visualization: Optional[Visualization]
    summary: Optional[str]
    error: Optional[str]
    is_query_relevant: bool
    is_result_relevant: bool
    regenerate_list: List[str]
    reanalyze_list: List[str]
    reflection: Optional[Dict[str, Any]]
    reflected_generated_sql: Optional[ReflectedGeneratedSQL]
    relevant_memories: Optional[List[Dict[str, Any]]]
    session_id: str
    sql_correction: Optional[SQLCorrectionResult]
 


