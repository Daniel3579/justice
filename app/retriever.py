from db import load_chroma_db
from config import TOP_K_LOCAL

_db = None

def get_local_retriever():
    global _db
    if _db is None:
        _db = load_chroma_db()
    return _db.as_retriever(search_kwargs={"k": TOP_K_LOCAL})