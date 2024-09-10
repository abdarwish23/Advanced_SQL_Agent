# app/services/database_service.py
from sqlalchemy import create_engine, inspect
from app.config import Config
from app.models import TableInfo, TableSchema, TableSample

class DatabaseService:
    @staticmethod
    def get_database_info(state):
        print("=================== Getting db info =====================")
        engine = create_engine(Config.DATABASE_URL)
        inspector = inspect(engine)
        table_info = {}

        for table_name in inspector.get_table_names():
            columns = {col['name']: str(col['type']) for col in inspector.get_columns(table_name)}
            table_info[table_name] = TableInfo(
                table_schema=TableSchema(name=table_name, columns=columns),
                sample=TableSample(name=table_name, data=[])
            )

        state["db_info"] = table_info
        return state
