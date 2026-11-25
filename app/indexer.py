import logging
import threading
from datetime import datetime, timezone

from db import load_documents
from retriever import drop_store, get_store

# переиндексация БД хрома
BATCH_SIZE = 200

_lock = threading.Lock()
_state = {"state": "idle", "started_at": None, "finished_at": None, "chunks": None, "error": None}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def status() -> dict:
    with _lock:
        return dict(_state)


def start() -> bool:
    with _lock:
        if _state["state"] == "running":
            return False
        _state.update(state="running", started_at=_now(), finished_at=None, chunks=None, error=None)
    threading.Thread(target=_run, daemon=True).start()
    return True


def _reset(store):
    try:
        store.reset_collection()
        return store
    except AttributeError:
        store.delete_collection()
        drop_store()
        return get_store()


def _run():
    try:
        documents = load_documents()
        store = _reset(get_store())
        for i in range(0, len(documents), BATCH_SIZE):
            store.add_documents(documents[i:i + BATCH_SIZE])
        with _lock:
            _state.update(state="done", finished_at=_now(), chunks=len(documents))
        logging.info(f"Переиндексация завершена: {len(documents)} чанков")
    except Exception as e:
        logging.exception("Ошибка переиндексации")
        with _lock:
            _state.update(state="error", finished_at=_now(), error=str(e))
