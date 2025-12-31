import duckdb
from src.config import DB_PATH


def get_db_connection():
    """
    Get a DuckDB database connection.
    """
    con = duckdb.connect(DB_PATH)
    return con
