from src.db.duckdb_conn import get_db_connection


class MorphAnalysisTool:
    def __init__(self):
        self.name = "MorphologicalAnalysis"

    def run(self, word: str) -> dict:
        """
        Input: A single Sanskrit word (e.g., "sPuratu")
        Output: Lemma and POS/morph tags.

        Example output:
        {
            "found": True,
            "word": "sPuratu",
            "analyses": [
                {"lemma": "sPur", "tags": "pos=v,p=3..."},
                ...
            ]
        }
        """
        if not word or not word.strip():
            return {"found": False, "error": "Empty input word."}

        word = word.strip()
        con = get_db_connection()

        try:
            # Look up analysis records for this word in the corpus.
            # We search both exact match and case-insensitive match.
            rows = con.execute(
                """
                SELECT lemma, pos_tag
                FROM morph_analysis
                WHERE word = ? OR word ILIKE ?
                LIMIT 5
                """,
                [word, word],
            ).fetchall()

        finally:
            con.close()

        if not rows:
            return {"found": False, "word": word}

        # Deduplicate: a word may have multiple analyses; also avoid duplicates.
        unique_results = list({(lemma, tag) for lemma, tag in rows})

        return {
            "found": True,
            "word": word,
            "analyses": [{"lemma": lemma, "tags": tag} for lemma, tag in unique_results],
        }
