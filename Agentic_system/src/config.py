import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = os.path.join(PROJECT_ROOT, "translation.duckdb")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models/Qwen2.5-7B-Instruct/")

os.makedirs(os.path.join(PROJECT_ROOT, "outputs"), exist_ok=True)
