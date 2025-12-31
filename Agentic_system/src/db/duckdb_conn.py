import duckdb
from src.config import DB_PATH

def get_db_connection():
    """获取 DuckDB 连接"""
    con = duckdb.connect(DB_PATH)
    return con