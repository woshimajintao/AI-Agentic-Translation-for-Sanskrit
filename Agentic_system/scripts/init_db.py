import sys
import os
sys.path.append(os.getcwd()) 

from src.db.duckdb_conn import get_db_connection
from src.db.schema import INIT_SQL

def init_db():
    print("Initializing Database...")
    con = get_db_connection()
    con.execute(INIT_SQL)
    
    con.execute("DELETE FROM mw_lexicon WHERE lemma = 'dharma'")
    con.execute("""
        INSERT INTO mw_lexicon (lemma, gloss, raw_entry) 
        VALUES ('dharma', 'law; usage; custom; duty; religion', 'dharma raw entry...')
    """)
    print("Database initialized at translation.duckdb")
    con.close()

if __name__ == "__main__":
    init_db()
