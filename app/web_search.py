from ddgs import DDGS
from config import TOP_K_WEB
import logging
import time

def web_search(query: str, max_results: int = TOP_K_WEB, retries: int = 2):
    # поиск в интернете 2 попытки
    for attempt in range(retries + 1):
        try:
            with DDGS(timeout=20) as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if results:
                return results
        except Exception as e:
            logging.warning(f"Веб-поиск попытка {attempt + 1}: {e}")
            if attempt < retries:
                time.sleep(2)
    logging.warning(f"Веб-поиск не дал результатов после {retries} попыток")
    return []


def format_web_results(results):
    # передача текста в промпт
    if not results:
        return "Интернет-поиск не дал результатов."

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        body = r.get("body", "")
        url = r.get("href", "")
        lines.append(f"[WEB-{i}] {title}\n{body}\nИсточник: {url}")
    return "\n\n".join(lines)