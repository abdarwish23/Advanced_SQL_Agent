# app/services/visualizer_service.py

# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# from io import BytesIO
# import base64
# from app.models import Visualization, AgentState
# from app.utils.llm_utils import get_llm
# from langchain.prompts import ChatPromptTemplate
# import json
# import logging

# logger = logging.getLogger(__name__)

# def visualization_check(state: AgentState) -> AgentState:
#     print("=================== Visualization Checkpoint =====================")
#     return state

# def create_visualization(data, query, visualization_type, x_column, y_column=None, title=None, palette='bright', style='whitegrid'):
#     df = pd.DataFrame(data)
#     sns.set_style(style)
#     sns.set_palette(palette)
#     plt.figure(figsize=(10, 6))

#     # Check if y_column is provided and valid
#     y_column_provided = y_column and y_column.strip() and y_column in df.columns
    
#     if not y_column_provided:
#         # Adjust visualization types that don't require y_column
#         if visualization_type in ["bar", "line", "scatter", "box"]:
#             y_column = x_column
#             x_column = df.index.name if df.index.name else 'Index'
#         elif visualization_type == "pie":
#             plt.pie(df[x_column], labels=df.index, autopct='%1.1f%%')
#         elif visualization_type == "histogram":
#             sns.histplot(data=df, x=x_column)
#         elif visualization_type == "heatmap":
#             sns.heatmap(df.corr(), annot=True, cmap='YlGnBu')
#         else:
#             raise ValueError(f"Unsupported visualization type without y_column: {visualization_type}")
#     else:
#         # Proceed with original logic for visualizations with y_column
#         if visualization_type == "bar":
#             sns.barplot(data=df, x=x_column, y=y_column)
#         elif visualization_type == "line":
#             sns.lineplot(data=df, x=x_column, y=y_column)
#         elif visualization_type == "scatter":
#             sns.scatterplot(data=df, x=x_column, y=y_column)
#         elif visualization_type == "pie":
#             plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
#         elif visualization_type == "histogram":
#             sns.histplot(data=df, x=x_column, y=y_column)
#         elif visualization_type == "box":
#             sns.boxplot(data=df, x=x_column, y=y_column)
#         elif visualization_type == "heatmap":
#             sns.heatmap(df.pivot(x_column, y_column, values=df.columns[-1]), annot=True, cmap='YlGnBu')
#         else:
#             raise ValueError(f"Unsupported visualization type: {visualization_type}")

#     plt.title(title or f"Visualization for: {query}")
#     plt.tight_layout()

#     buffer = BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#     image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
#     plt.close()

#     if y_column_provided:
#         description = f"{visualization_type.capitalize()} chart visualization of {x_column} vs {y_column} for the query: {query}"
#     else:
#         description = f"{visualization_type.capitalize()} chart visualization of {x_column} for the query: {query}"
    
#     return Visualization(image=image_base64, description=description)

# def select_visualization(state: AgentState) -> dict:
#     llm = get_llm("openai","gpt-3.5-turbo")
    
#     prompt = ChatPromptTemplate.from_template("""
#     Given the following information:
#     1. Original user query: {user_query}
#     2. Analyzed query: {analyzed_query}
#     3. SQL query executed: {sql_query}
#     4. Query execution result (first 5 rows): {sample_data}
#     5. Data columns and types: {data_types}

#     You are an expert data analyst. Select the most appropriate visualization type and parameters to best represent the data and answer the user's query.
#     Consider the data types, the number of data points, and the nature of the question being asked.

#     Respond in the following JSON format:
#     {{
#         "visualization_type": "bar|line|scatter|pie|histogram|box|heatmap",
#         "x_column": "name of the column for x-axis",
#         "y_column": "name of the column for y-axis (if applicable)",
#         "title": "A descriptive title for the visualization",
#         "explanation": "A brief explanation of why this visualization was chosen"
#     }}
#     """)

#     df = pd.DataFrame(state["execution_result"].data)
#     sample_data = df.head().to_dict()
#     data_types = df.dtypes.to_dict()

#     chain = prompt | llm

#     try:
#         response = chain.invoke({
#             "user_query": state["user_query"],
#             "analyzed_query": state["analyzed_query"].analyzed_query,
#             "sql_query": state["generated_sql"].sql_query,
#             "sample_data": json.dumps(sample_data),
#             "data_types": str(data_types)
#         })
        
#         visualization_params = json.loads(response.content)
#         logger.info(f"Selected visualization: {visualization_params}")
#         return visualization_params
#     except Exception as e:
#         logger.error(f"Error in visualization selection: {str(e)}")
#         return {"visualization_type": "bar", "x_column": df.columns[0], "y_column": df.columns[1] if len(df.columns) > 1 else None}

# def data_visualizer(state: AgentState) -> AgentState:
#     print("=================== Data Visualization =====================")
#     if not state["execution_result"].success or not state["evaluation_result"].requires_visualization:
#         state["visualization"] = None
#     else:
#         visualization_params = select_visualization(state)
#         state["visualization"] = create_visualization(
#             state["execution_result"].data,
#             state["analyzed_query"].original_query,
#             visualization_params["visualization_type"],
#             visualization_params["x_column"],
#             visualization_params.get("y_column"),
#             visualization_params.get("title")
#         )
#         state["visualization_explanation"] = visualization_params.get("explanation", "")
#     return state



# app/services/visualizer_service.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from app.models import Visualization, AgentState
from app.utils.llm_utils import get_llm
from langchain.prompts import ChatPromptTemplate
import json
import logging
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

def visualization_check(state: AgentState) -> AgentState:
    print("=================== Visualization Checkpoint =====================")
    return state

def create_visualization(data, query, visualization_type, x_column, y_column=None, title=None, palette='viridis', style='darkgrid'):
    df = pd.DataFrame(data)
    sns.set_style(style)
    sns.set_palette(palette)
    plt.figure(figsize=(12, 7))

    # Check if x_column is a datetime
    is_time_series = pd.api.types.is_datetime64_any_dtype(df[x_column])
    if is_time_series:
        df[x_column] = pd.to_datetime(df[x_column])

    # Check if y_column is provided and valid
    y_column_provided = y_column and y_column.strip() and y_column in df.columns
    
    if not y_column_provided:
        y_column = x_column
        x_column = df.index.name if df.index.name else 'Index'

    if visualization_type == "bar":
        ax = sns.barplot(data=df, x=x_column, y=y_column)
        plt.xticks(rotation=45, ha='right')
    elif visualization_type == "line":
        ax = sns.lineplot(data=df, x=x_column, y=y_column, marker='o')
        plt.plot(df[x_column], df[y_column], alpha=0)  # This creates anchor points for the spline
        if is_time_series:
            plt.gcf().autofmt_xdate()
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    elif visualization_type == "scatter":
        ax = sns.scatterplot(data=df, x=x_column, y=y_column)
    elif visualization_type == "pie":
        plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.5))
        plt.axis('equal')
    elif visualization_type == "histogram":
        ax = sns.histplot(data=df, x=x_column, y=y_column, kde=True)
    elif visualization_type == "box":
        ax = sns.boxplot(data=df, x=x_column, y=y_column)
        plt.xticks(rotation=45, ha='right')
    elif visualization_type == "heatmap":
        ax = sns.heatmap(df.pivot(x_column, y_column, values=df.columns[-1]), annot=True, cmap='YlGnBu')
    else:
        raise ValueError(f"Unsupported visualization type: {visualization_type}")

    plt.title(title or f"Visualization for: {query}", fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()

    # Add some styling to make the plot more visually appealing
    if visualization_type != "pie":
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_linewidth(0.5)
        
    for spine in plt.gca().spines.values():
        spine.set_edgecolor('#888888')

    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Make the plot area have rounded corners
    plt.gca().patch.set_facecolor('#F0F0F0')
    plt.gcf().patch.set_facecolor('white')
    plt.gca().patch.set_alpha(0.3)
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    if y_column_provided:
        description = f"{visualization_type.capitalize()} chart visualization of {x_column} vs {y_column} for the query: {query}"
    else:
        description = f"{visualization_type.capitalize()} chart visualization of {x_column} for the query: {query}"
    
    return Visualization(image=image_base64, description=description)

def select_visualization(state: AgentState) -> dict:
    llm = get_llm("openai","gpt-3.5-turbo")
    
    prompt = ChatPromptTemplate.from_template("""
    Given the following information:
    1. Original user query: {user_query}
    2. Analyzed query: {analyzed_query}
    3. SQL query executed: {sql_query}
    4. Query execution result (first 5 rows): {sample_data}
    5. Data columns and types: {data_types}

    You are an expert data analyst. Select the most appropriate visualization type and parameters to best represent the data and answer the user's query.
    Consider the data types, the number of data points, and the nature of the question being asked.
    If there's a date or time column, consider using it for the x-axis in a time series visualization.

    Respond in the following JSON format:
    {{
        "visualization_type": "bar|line|scatter|pie|histogram|box|heatmap",
        "x_column": "name of the column for x-axis",
        "y_column": "name of the column for y-axis (if applicable)",
        "title": "A descriptive title for the visualization",
        "explanation": "A brief explanation of why this visualization was chosen"
    }}
    """)

    df = pd.DataFrame(state["execution_result"].data)
    sample_data = df.head().to_dict()
    data_types = df.dtypes.to_dict()

    chain = prompt | llm

    try:
        response = chain.invoke({
            "user_query": state["user_query"],
            "analyzed_query": state["analyzed_query"].analyzed_query,
            "sql_query": state["generated_sql"].sql_query,
            "sample_data": json.dumps(sample_data),
            "data_types": str(data_types)
        })
        
        visualization_params = json.loads(response.content)
        logger.info(f"Selected visualization: {visualization_params}")
        return visualization_params
    except Exception as e:
        logger.error(f"Error in visualization selection: {str(e)}")
        return {"visualization_type": "bar", "x_column": df.columns[0], "y_column": df.columns[1] if len(df.columns) > 1 else None}

def data_visualizer(state: AgentState) -> AgentState:
    print("=================== Data Visualization =====================")
    if not state["execution_result"].success or not state["evaluation_result"].requires_visualization:
        state["visualization"] = None
    else:
        visualization_params = select_visualization(state)
        state["visualization"] = create_visualization(
            state["execution_result"].data,
            state["analyzed_query"].original_query,
            visualization_params["visualization_type"],
            visualization_params["x_column"],
            visualization_params.get("y_column"),
            visualization_params.get("title")
        )
        state["visualization_explanation"] = visualization_params.get("explanation", "")
    return state