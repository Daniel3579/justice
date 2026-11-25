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

# БД Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://justice:justice@localhost:5432/justice")
# LEGACY_SQLITE_PATH = BASE_DIR / "data" / "app.db"
MIN_PASSWORD_LENGTH = 6
ADMIN_EMAILS = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]

APP_URL = os.getenv("APP_URL", "http://localhost:8080").rstrip("/")
RESET_TOKEN_TTL_MINUTES = 60
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER

MAX_UPLOAD_MB = 50
PDF_FONT_REGULAR = os.getenv("PDF_FONT_REGULAR", "")
PDF_FONT_BOLD = os.getenv("PDF_FONT_BOLD", "")
