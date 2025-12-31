# scripts/ingest_all.py

import sys
import os
import glob
import xml.etree.ElementTree as ET
from pathlib import Path
from tqdm import tqdm # 建议 pip install tqdm 看进度

# 路径设置
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"

from src.db.duckdb_conn import get_db_connection
from src.db.schema import INIT_SQL

def init_db_tables():
    """确保表已创建"""
    con = get_db_connection()
    con.execute(INIT_SQL)
    con.close()

# ---------------------------------------------------------
# 1. 解析 MW 字典 (mw.xml)
# ---------------------------------------------------------
def ingest_mw_dict():
    xml_path = DATA_DIR / "mw_dict" / "mw.xml"
    if not xml_path.exists():
        print(f"❌ MW XML not found at {xml_path}")
        return

    print(f"--> Parsing MW Dictionary: {xml_path}")
    con = get_db_connection()
    con.execute("DELETE FROM mw_lexicon") # 清空旧数据

    # 使用 iterparse 节省内存，因为 mw.xml 很大
    context = ET.iterparse(xml_path, events=("end",))
    
    batch_data = []
    batch_size = 5000
    
    count = 0
    for event, elem in tqdm(context, desc="Ingesting MW"):
        if elem.tag == 'H1':
            # 提取 lemma (key1)
            h_tag = elem.find('h')
            if h_tag is not None:
                key1 = h_tag.find('key1')
                lemma = key1.text if key1 is not None else None
                
                # 提取 body (释义)
                body_tag = elem.find('body')
                # 简单处理：获取所有文本内容，忽略 HTML 标签
                gloss = "".join(body_tag.itertext()) if body_tag is not None else ""
                
                # 保存原始 XML
                raw_xml = ET.tostring(elem, encoding='unicode')

                if lemma:
                    batch_data.append((lemma, gloss, raw_xml))
            
            # 释放内存
            elem.clear()

        # 批量插入
        if len(batch_data) >= batch_size:
            con.executemany("INSERT INTO mw_lexicon (lemma, gloss, raw_xml) VALUES (?, ?, ?)", batch_data)
            count += len(batch_data)
            batch_data = []

    # 插入剩余数据
    if batch_data:
        con.executemany("INSERT INTO mw_lexicon (lemma, gloss, raw_xml) VALUES (?, ?, ?)", batch_data)
        count += len(batch_data)

    print(f"✅ Inserted {count} dictionary entries.")
    con.close()

# ---------------------------------------------------------
# 2. 解析 Ambuda (CoNLL-like txt)
# ---------------------------------------------------------
def ingest_ambuda():
    # 查找 ambuda-dcs 目录下所有的 .txt 文件
    txt_files = glob.glob(str(DATA_DIR / "ambuda-dcs" / "*.txt"))
    if not txt_files:
        print("❌ No Ambuda .txt files found.")
        return

    print(f"--> Parsing Ambuda Grammar Files: {len(txt_files)} files found.")
    con = get_db_connection()
    con.execute("DELETE FROM morph_analysis")

    batch_data = []
    total_lines = 0

    for file_path in txt_files:
        current_sent_id = "unknown"
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: 
                    continue
                
                # 处理 ID 行: # id = HamDu.1
                if line.startswith("# id"):
                    parts = line.split("=")
                    if len(parts) > 1:
                        current_sent_id = parts[1].strip()
                    continue
                
                # 处理数据行: dukUlam  dukUla  pos=n,g=n...
                # 可能是 Tab 分隔，也可能是多个空格
                # 先尝试用 tab 分割
                parts = line.split('\t')
                if len(parts) < 3:
                    # 如果不是 tab，尝试空格
                    parts = line.split()
                
                if len(parts) >= 3:
                    word = parts[0].strip()
                    lemma = parts[1].strip()
                    pos_tag = parts[2].strip()
                    
                    batch_data.append((word, lemma, pos_tag, current_sent_id))

                if len(batch_data) >= 10000:
                    con.executemany("INSERT INTO morph_analysis (word, lemma, pos_tag, sent_id) VALUES (?, ?, ?, ?)", batch_data)
                    total_lines += len(batch_data)
                    batch_data = []

    if batch_data:
        con.executemany("INSERT INTO morph_analysis (word, lemma, pos_tag, sent_id) VALUES (?, ?, ?, ?)", batch_data)
        total_lines += len(batch_data)

    print(f"✅ Inserted {total_lines} morph analysis records.")
    con.close()

# ---------------------------------------------------------
# 3. 解析 Testsets (MKB Parallel)
# ---------------------------------------------------------
def ingest_mkb_testset():
    mkb_dir = DATA_DIR / "testsets" / "mkb"
    sa_path = mkb_dir / "mkb.sa"
    en_path = mkb_dir / "mkb.en"

    if not sa_path.exists() or not en_path.exists():
        print(f"❌ MKB files not found in {mkb_dir}")
        return

    print(f"--> Parsing MKB Testset...")
    con = get_db_connection()
    con.execute("DELETE FROM dataset_items WHERE dataset_name='mkb'")

    # 平行读取两个文件
    with open(sa_path, 'r', encoding='utf-8') as f_sa, \
         open(en_path, 'r', encoding='utf-8') as f_en:
        
        sa_lines = f_sa.readlines()
        en_lines = f_en.readlines()

        if len(sa_lines) != len(en_lines):
            print(f"⚠️ Warning: Line counts mismatch! SA: {len(sa_lines)}, EN: {len(en_lines)}")
        
        # 取最小长度，防止越界
        min_len = min(len(sa_lines), len(en_lines))
        
        batch_data = []
        for i in range(min_len):
            src = sa_lines[i].strip()
            tgt = en_lines[i].strip()
            if src: # 忽略空行
                batch_data.append(('mkb', i+1, src, tgt))

        con.executemany("INSERT INTO dataset_items (dataset_name, item_id, src_text, tgt_text) VALUES (?, ?, ?, ?)", batch_data)
        print(f"✅ Inserted {len(batch_data)} test pairs from MKB.")

    con.close()

if __name__ == "__main__":
    init_db_tables()
    ingest_mw_dict()
    ingest_ambuda()
    ingest_mkb_testset()
    print("\n🎉 All Data Ingestion Complete!")