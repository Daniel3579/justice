from config import TOP_K_LOCAL
from db import load_chroma_db

_store = None


def get_store():
    global _store
    if _store is None:
        _store = load_chroma_db()
    return _store


def drop_store():
    global _store
    _store = None


def get_local_retriever():
    return get_store().as_retriever(search_kwargs={"k": TOP_K_LOCAL})
