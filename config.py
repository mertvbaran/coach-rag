import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SAMPLE_DIR = DATA_DIR / "sample"
INDEX_DIR = DATA_DIR / "index"
CACHE_DIR = DATA_DIR / "cache"
RESULTS_DIR = Path(__file__).parent / "results"

# Falls back to the bundled sample data when COACH_VAULT_PATH isn't set, so
# the pipeline runs end-to-end with no external vault required.
VAULT_ROOT = Path(os.environ.get("COACH_VAULT_PATH", SAMPLE_DIR))
VAULT_DIRS = ("concepts", "sources", "flashcards")

EMBEDDING_MODEL_ALIAS = "qwen3-embedding-0.6b"
CHAT_MODEL_ALIAS = "qwen2.5-0.5b"

EMBEDDING_BATCH_SIZE = 16
TOP_K = 5
