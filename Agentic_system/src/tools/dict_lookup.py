from src.db.duckdb_conn import get_db_connection
from indic_transliteration import sanscript


class DictionaryLookupTool:
    def __init__(self):
        self.name = "DictionaryLookup"
        # Slightly higher truncation limit because we will later summarize with an LLM
        # and want to keep more context.
        self.TRUNCATE_LIMIT = 2000

    def _to_iast(self, text: str) -> str:
        """Transliterate Devanagari -> IAST."""
        try:
            return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
        except Exception:
            return text

    def _generate_heuristic_candidates(self, word: str) -> list[str]:
        """
        Heuristic lemmatization: based on common Sanskrit inflectional suffixes,
        generate possible lemma candidates (a simple rule-based stemmer).
        """
        candidates: set[str] = set()
        candidates.add(word)  # Always include the original word

        # Common suffix mapping (Suffix -> Replacement)
        # Covers frequent declensional patterns (a-stem, i-stem, u-stem, etc.)
        suffixes: list[tuple[str, str]] = [
            # Case endings for -a stems (e.g., rāmasya, rāmānām, rāmeṇa...)
            ("asya", "a"),
            ("ānām", "a"),
            ("ena", "a"),
            ("āt", "a"),
            ("āya", "a"),
            ("aiḥ", "a"),
            ("ebhyaḥ", "a"),
            ("eṣu", "a"),
            ("au", "a"),
            # Visarga handling (very simple)
            ("ḥ", ""),
            ("ḥ", "s"),
            ("ḥ", "r"),
            ("o", "a"),
            # Anusvara / accusative
            ("am", "a"),
            ("m", "a"),
            # Plural / dual
            ("āḥ", "a"),
            ("āni", "a"),
            # Consonant stems or feminine patterns (very approximate)
            ("yāḥ", "ī"),
            ("yā", "ī"),
            ("īnām", "in"),
            ("iḥ", "i"),
            # Verb endings (very basic)
            ("ti", ""),
            ("nti", ""),
            ("si", ""),
            ("mi", ""),
            ("tu", ""),
            ("ntu", ""),
            ("tvā", ""),
        ]

        for suffix, replacement in suffixes:
            if word.endswith(suffix):
                # Option 1: remove suffix and add replacement
                stem = word[: -len(suffix)] + replacement
                candidates.add(stem)
                # Option 2: remove suffix only (root-like form)
                candidates.add(word[: -len(suffix)])

        return list(candidates)

    def run(self, words: list[str]) -> dict[str, str]:
        if not words:
            return {}

        unique_words = list({w.strip() for w in words if w and w.strip()})
        if not unique_words:
            return {}

        con = get_db_connection()
        results: dict[str, str] = {}

        try:
            for w in unique_words:
                # 1) Preprocess: transliterate to IAST if input is Devanagari
                iast_word = w
                if any("\u0900" <= ch <= "\u097F" for ch in w):
                    iast_word = self._to_iast(w)

                # 2) Generate candidate lemmas (heuristics)
                candidates = self._generate_heuristic_candidates(iast_word)
                found_entry = None

                # 3) Strategy A: Exact match over all candidates via a single IN query
                placeholders = ",".join(["?"] * len(candidates))
                query = f"""
                    SELECT lemma, gloss, raw_xml
                    FROM mw_lexicon
                    WHERE lemma IN ({placeholders})
                    ORDER BY length(lemma) ASC
                    LIMIT 1
                """
                res = con.execute(query, candidates).fetchone()
                if res:
                    found_entry = res

                # 4) Strategy B: If still not found, try a prefix match (very light fuzzy)
                # Example: if 'dharmasya' is not found, try 'dharma%'
                if not found_entry and len(iast_word) > 3:
                    prefix = iast_word[:5]  # use first 4–5 chars for fuzzy search
                    fuzzy_res = con.execute(
                        """
                        SELECT lemma, gloss, raw_xml
                        FROM mw_lexicon
                        WHERE lemma ILIKE ?
                        LIMIT 1
                        """,
                        [f"{prefix}%"],
                    ).fetchone()
                    if fuzzy_res:
                        found_entry = fuzzy_res

                # 5) Format output
                if found_entry:
                    lemma_found, gloss, raw = found_entry
                    content = gloss if gloss else raw
                    if not content:
                        content = "Entry found but empty."

                    # Truncate to avoid huge outputs (later steps can compress/summarize)
                    if len(content) > self.TRUNCATE_LIMIT:
                        content = content[: self.TRUNCATE_LIMIT] + "... [truncated]"

                    # Indicate which lemma variant matched
                    results[w] = f"[Matched Lemma: {lemma_found}]\n{content}"
                else:
                    results[w] = "No entry found"

        except Exception as e:
            print(f"Error in dictionary lookup: {e}")
            results["error"] = str(e)
        finally:
            con.close()

        return results
