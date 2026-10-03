import logging
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser

from config import LLM_MODEL
from prompts import EXTRACT_PROMPT, ISK_PROMPT
from retriever import get_local_retriever
from web_search import web_search, format_web_results

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = Ollama(model=LLM_MODEL, temperature=0.2)
    return _llm


def extract_facts(user_text: str) -> str:
    """Шаг 1: превращаем неформальный текст в структурированную фабулу."""
    chain = EXTRACT_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({"user_text": user_text})


def gather_norms(facts: str) -> tuple[str, str]:
    """Шаг 2: собираем нормы из локальной базы и из интернета."""
    # Локальная база
    retriever = get_local_retriever()
    docs = retriever.invoke(facts)

    local_parts = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "локальный документ")
        local_parts.append(f"[НОРМА-{i}] (источник: {src})\n{d.page_content}")
    local_norms = "\n\n".join(local_parts) if local_parts else "Локальных норм не найдено."

    # Интернет — ищем по ключевым словам из фабулы
    query = _build_web_query(facts)
    web_results = web_search(query)
    web_norms = format_web_results(web_results)

    return local_norms, web_norms


def _build_web_query(facts: str) -> str:
    """Делает поисковый запрос из фабулы."""
    # Простая эвристика: берём первые строки + ключевые слова
    keywords = []
    for line in facts.splitlines():
        low = line.lower()
        if any(k in low for k in ["просрочк", "недостат", "непостав", "возврат", "неустойк"]):
            keywords.append(line.strip())
    base = "защита прав потребителей иск " + " ".join(keywords[:3])
    return base.strip() or "защита прав потребителей исковое заявление образец"


def generate_isk(user_text: str) -> dict:
    """Полный пайплайн."""
    logging.info("Шаг 1: извлечение фактов")
    facts = extract_facts(user_text)

    logging.info("Шаг 2: сбор норм")
    local_norms, web_norms = gather_norms(facts)

    logging.info("Шаг 3: генерация иска")
    chain = ISK_PROMPT | get_llm() | StrOutputParser()
    isk = chain.invoke({
        "facts": facts,
        "local_norms": local_norms,
        "web_norms": web_norms,
    })

    return {
        "facts": facts,
        "local_norms": local_norms,
        "web_norms": web_norms,
        "isk": isk,
    }