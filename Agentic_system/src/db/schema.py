# src/db/schema.py

INIT_SQL = """
-- 1. 词典表 (Monier-Williams)
-- 使用 FTS (Full Text Search) 索引 gloss 字段以便英文反查，或者仅对 lemma 建索引
CREATE TABLE IF NOT EXISTS mw_lexicon (
    lemma VARCHAR,       -- 词头 (如 dharma)
    gloss VARCHAR,       -- 释义内容
    raw_xml VARCHAR,     -- 原始 XML (保留格式)
    source VARCHAR DEFAULT 'MW'
);

-- 2. 词法/语法分析表 (Ambuda)
-- 用于把“变形词”映射回“原形”
CREATE TABLE IF NOT EXISTS morph_analysis (
    word VARCHAR,        -- 变形后的词 (如 sPuratu)
    lemma VARCHAR,       -- 原形 (如 sPur)
    pos_tag VARCHAR,     -- 词性/语法标记 (pos=v,p=3...)
    sent_id VARCHAR      -- 来源句 ID
);

-- 3. 数据集表 (MKB Testset)
CREATE TABLE IF NOT EXISTS dataset_items (
    dataset_name VARCHAR, -- 'mkb'
    item_id INTEGER,
    src_text VARCHAR,     -- Sanskrit
    tgt_text VARCHAR      -- English Reference
);

-- 4. 运行记录表 (保持不变)
CREATE TABLE IF NOT EXISTS translations (
    run_id VARCHAR,
    timestamp TIMESTAMP,
    mode VARCHAR,
    src_text VARCHAR,
    final_text VARCHAR,
    tool_calls_json JSON,
    step_summaries_json JSON
);
"""