from src.db.duckdb_conn import get_db_connection
import re

class GlossaryLookupTool:
    def __init__(self):
        self.name = "GlossaryLookup"
    
    def run(self, text: str) -> dict:
        """
        Input: Full source text
        Output: Dict {sanskrit_term: official_english_definition}
        
        Logic:
        1. 简单的分词。
        2. 在 glossary 表中查找是否存在这些词（不区分大小写）。
        3. 返回强制性的定义/译法。
        """
        if not text:
            return {}

        # 简单的预处理：提取单词，去除标点
        # 允许连字符，因为梵语转写常有 dharma-ksetre
        words = set(re.findall(r"\b[a-zA-Z\u00C0-\u00FF]+\b", text))
        
        if not words:
            return {}

        con = get_db_connection()
        results = {}
        
        try:
            # 构建查询：查找所有匹配的术语
            # 注意：Glossary 通常是精确匹配词头
            placeholders = ','.join(['?'] * len(words))
            
            # 我们查找 term 在单词列表里的项
            # COLLATE NOCASE 用于忽略大小写
            query = f"""
                SELECT term, definition 
                FROM glossary 
                WHERE term COLLATE NOCASE IN ({placeholders})
            """
            
            rows = con.execute(query, list(words)).fetchall()
            
            for row in rows:
                term = row[0]
                defn = row[1]
                # 简单的清洗，去掉过长的解释，只保留核心定义（视 PDF 内容而定）
                # 这里保留原貌，因为 PDF 里的定义看起来像是解释性的
                results[term] = defn.strip()
                
        except Exception as e:
            # 如果表不存在（还没上传过），这就不是错误，只是没数据
            if "Table with name glossary does not exist" not in str(e):
                print(f"Glossary Error: {e}")
        finally:
            con.close()
            
        return results