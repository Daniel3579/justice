from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

DOCUMENTS_PATH = BASE_DIR / "data" / "documents"
CHROMA_DB_PATH = BASE_DIR / "data" / "chroma_db"
TEMPLATES_PATH = APP_DIR / "templates"
ISK_TEMPLATE = "isk.j2"

# по умолчанию
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:4b") # изменена модель на более легкую для тестирования
NUM_CTX = 8192
KEEP_ALIVE = "15m"
LLM_TIMEOUT = 600
MAX_TOKENS_JSON = 1500
MAX_TOKENS_TEXT = 800

CHUNK_SIZE = 1000 # изменен метод разбивки => размер чанка
CHUNK_OVERLAP = 100
TOP_K_LOCAL = 3
TOP_K_WEB = 3
WEB_SEARCH_ENABLED = True # можно вкл выкл для тестирования

HISTORY_TURNS = 8
MAX_MESSAGE_CHARS = 8000

# БД SQLite
APP_DB_PATH = BASE_DIR / "data" / "app.db"
MIN_PASSWORD_LENGTH = 6