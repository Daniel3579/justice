import logging

import uvicorn

from config import CHROMA_DB_PATH, DOCUMENTS_PATH

logging.basicConfig(level=logging.INFO)


# флаг сборки базы
def has_documents() -> bool:
    return DOCUMENTS_PATH.exists() and any(DOCUMENTS_PATH.rglob("*.pdf"))


if __name__ == "__main__":
    if not CHROMA_DB_PATH.exists():
        if has_documents():
            logging.info("Векторной базы нет, сборка из data/documents")
            from db import build_chroma_db

            build_chroma_db()
        else:
            logging.warning("Нет базы или документов, поиск без норм")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)