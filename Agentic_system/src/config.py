import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = os.path.join(PROJECT_ROOT, "translation.duckdb")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models/Qwen2.5-7B-Instruct/")

# 确保输出目录存在
os.makedirs(os.path.join(PROJECT_ROOT, "outputs"), exist_ok=True)