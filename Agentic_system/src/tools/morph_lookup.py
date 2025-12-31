from src.db.duckdb_conn import get_db_connection

class MorphAnalysisTool:
    def __init__(self):
        self.name = "MorphologicalAnalysis"

    def run(self, word: str) -> dict:
        """
        Input: A single Sanskrit word (e.g., 'sPuratu')
        Output: Lemma and POS tags (e.g., {'lemma': 'sPur', 'tags': 'pos=v,p=3...'})
        """
        con = get_db_connection()
        # 查找该词在语料库中出现过的分析记录
        rows = con.execute("""
            SELECT lemma, pos_tag 
            FROM morph_analysis 
            WHERE word = ? OR word ILIKE ?
            LIMIT 5
        """, [word, word]).fetchall()
        
        con.close()
        
        if not rows:
            return {"found": False}
        
        # 去重，可能同一个词有多种分析
        unique_results = list(set(rows))
        
        return {
            "found": True,
            "word": word,
            "analyses": [{"lemma": r[0], "tags": r[1]} for r in unique_results]
        }