# src/db/schema.py

INIT_SQL = """
-- 1. Dictionary table (Monier–Williams)
-- You may add an FTS (Full Text Search) index on the gloss field for English reverse lookup,
-- or keep indexing only on the lemma field.
CREATE TABLE IF NOT EXISTS mw_lexicon (
    lemma VARCHAR,       -- Headword (e.g., dharma)
    gloss VARCHAR,       -- Definition / gloss text
    raw_xml VARCHAR,     -- Original XML (preserved formatting)
    source VARCHAR DEFAULT 'MW'
);

-- 2. Morphological / grammatical analysis table (Ambuda)
-- Used to map inflected forms back to their base lemma.
CREATE TABLE IF NOT EXISTS morph_analysis (
    word VARCHAR,        -- Inflected form (e.g., sPuratu)
    lemma VARCHAR,       -- Base form / lemma (e.g., sPur)
    pos_tag VARCHAR,     -- POS / morphological tags (e.g., pos=v,p=3...)
    sent_id VARCHAR      -- Source sentence ID
);

-- 3. Dataset table (e.g., MKB Testset)
CREATE TABLE IF NOT EXISTS dataset_items (
    dataset_name VARCHAR, -- Dataset name (e.g., 'mkb')
    item_id INTEGER,
    src_text VARCHAR,     -- Sanskrit source text
    tgt_text VARCHAR      -- English reference translation
);

-- 4. Translation run log table (unchanged)
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
