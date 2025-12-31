from src.db.duckdb_conn import get_db_connection
from indic_transliteration import sanscript

class DictionaryLookupTool:
    def __init__(self):
        self.name = "DictionaryLookup"
        # 稍微放宽 SQL 截断限制，因为我们后面要用 LLM 做摘要，需要更多上下文
        self.TRUNCATE_LIMIT = 2000 

    def _to_iast(self, text: str) -> str:
        """转写：天城体 -> IAST"""
        try:
            return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
        except Exception:
            return text

    def _generate_heuristic_candidates(self, word: str) -> list:
        """
        启发式词形还原：基于常见的梵语屈折变化后缀，反推可能的 Lemma。
        这是一个简单的 Rule-based Stemmer。
        """
        candidates = set()
        candidates.add(word) # 原词肯定要查
        
        # 常见后缀映射 (Suffix -> Replacement)
        # 这涵盖了 a-stem, i-stem, u-stem 的常见变格
        suffixes = [
            # Case endings for -a stems (Ramah, Ramam, Ramena...)
            ("asya", "a"), ("ānām", "a"), ("ena", "a"), ("āt", "a"), ("āya", "a"),
            ("aiḥ", "a"), ("ebhyaḥ", "a"), ("eṣu", "a"), ("au", "a"), 
            # Visarga handling (simple)
            ("ḥ", ""), ("ḥ", "s"), ("ḥ", "r"), ("o", "a"), 
            # Anusvara
            ("am", "a"), ("m", "a"),
            # Plural / Dual
            ("āḥ", "a"), ("āni", "a"), 
            # Consonant stems or feminine
            ("yāḥ", "ī"), ("yā", "ī"), ("īnām", "in"), ("iḥ", "i"),
            # Verb endings (very basic)
            ("ti", ""), ("nti", ""), ("si", ""), ("mi", ""),
            ("tu", ""), ("ntu", ""), ("tvā", "")
        ]

        for suffix, replacement in suffixes:
            if word.endswith(suffix):
                # 尝试去掉后缀加上 replacement
                stem = word[:-len(suffix)] + replacement
                candidates.add(stem)
                # 同时也尝试直接去掉后缀 (root)
                candidates.add(word[:-len(suffix)])

        return list(candidates)

    def run(self, words: list) -> dict:
        if not words: return {}
        
        unique_words = list(set([w.strip() for w in words if w.strip()]))
        if not unique_words: return {}

        con = get_db_connection()
        results = {}
        
        try:
            for w in unique_words:
                # 1. 预处理：转写为 IAST
                iast_word = w
                if any('\u0900' <= char <= '\u097F' for char in w):
                    iast_word = self._to_iast(w)
                
                # 2. 生成候选词列表 (Heuristics)
                candidates = self._generate_heuristic_candidates(iast_word)
                
                found_entry = None
                
                # 3. 策略 A: 精确匹配 (Exact Match) - 遍历所有候选词
                # 我们构建一个 SQL `IN` 查询来一次性查完所有候选
                placeholders = ','.join(['?'] * len(candidates))
                query = f"""
                    SELECT lemma, gloss, raw_xml 
                    FROM mw_lexicon 
                    WHERE lemma IN ({placeholders})
                    -- 简单的排序：优先匹配长度接近的，或者按字母序
                    ORDER BY length(lemma) ASC
                    LIMIT 1
                """
                res = con.execute(query, candidates).fetchone()
                
                if res:
                    found_entry = res
                
                # 4. 策略 B: 如果都没查到，尝试前缀匹配 (Prefix Match / Fuzzy)
                # 比如 'dharmasya' 没查到，试着查 'dharm%'
                if not found_entry and len(iast_word) > 3:
                    # 只取前 4-5 个字母做模糊搜索
                    prefix = iast_word[:5] 
                    fuzzy_res = con.execute("""
                        SELECT lemma, gloss, raw_xml 
                        FROM mw_lexicon 
                        WHERE lemma ILIKE ? 
                        LIMIT 1
                    """, [f"{prefix}%"]).fetchone()
                    if fuzzy_res:
                        found_entry = fuzzy_res

                # 5. 格式化输出
                if found_entry:
                    lemma_found, gloss, raw = found_entry
                    content = gloss if gloss else raw
                    if not content: content = "Entry found but empty."
                    
                    # 截断防止爆显存 (但在 Step 3.5 我们会用 LLM 压缩它)
                    if len(content) > self.TRUNCATE_LIMIT:
                        content = content[:self.TRUNCATE_LIMIT] + "... [truncated]"
                    
                    # 标记一下我们是查哪个变体查到的
                    results[w] = f"[Matched Lemma: {lemma_found}]\n{content}"
                else:
                    results[w] = "No entry found"
                    
        except Exception as e:
            print(f"Error in Dict Lookup: {e}")
            results["error"] = str(e)
        finally:
            con.close()
            
        return results