from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
CHROMA_DB_PATH = BASE_DIR / "data" / "chroma_db"

EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "mistral"

TOP_K_LOCAL = 4
TOP_K_WEB = 3