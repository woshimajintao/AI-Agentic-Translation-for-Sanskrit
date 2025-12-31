from src.db.duckdb_conn import get_db_connection
import re


class GlossaryLookupTool:
    def __init__(self):
        self.name = "GlossaryLookup"

    def run(self, text: str) -> dict[str, str]:
        """
        Input: Full source text
        Output: A dict mapping {sanskrit_term: official_english_definition}

        Logic:
        1) Simple tokenization.
        2) Look up tokens in the `glossary` table (case-insensitive).
        3) Return mandatory / canonical definitions (preferred translations).
        """
        if not text:
            return {}

        # Simple preprocessing: extract words and remove punctuation.
        # We allow extended Latin characters (e.g., ā, ī, ū) commonly used in Sanskrit transliteration.
        words = set(re.findall(r"\b[a-zA-Z\u00C0-\u00FF]+\b", text))
        if not words:
            return {}

        con = get_db_connection()
        results: dict[str, str] = {}

        try:
            # Build a query that matches all candidate terms.
            # Glossary entries are typically exact headword matches.
            placeholders = ",".join(["?"] * len(words))

            # Use COLLATE NOCASE to ignore case in matching.
            query = f"""
                SELECT term, definition
                FROM glossary
                WHERE term COLLATE NOCASE IN ({placeholders})
            """

            rows = con.execute(query, list(words)).fetchall()

            for term, definition in rows:
                # Keep definitions as-is (you can add trimming/shortening if needed).
                results[term] = (definition or "").strip()

        except Exception as e:
            # If the table doesn't exist yet, treat it as "no data" rather than a hard error.
            if "Table with name glossary does not exist" not in str(e):
                print(f"Glossary lookup error: {e}")

        finally:
            con.close()

        return results
