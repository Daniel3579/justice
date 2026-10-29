import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from config import HISTORY_TURNS, WEB_SEARCH_ENABLED
from llm import chat
from prompts import ANSWER_PROMPT, COMPOSE_PROMPT, EXTRACT_PROMPT, INTENT_PROMPT
from render import build_context, find_missing, render_marked, strip_markers
from retriever import get_local_retriever
from schemas import CaseFacts, Composed
from web_search import web_search

# каждый запрос формируется из фактов + шаблонной фразы по типу 
VIOLATION_QUERIES = {
    "delay_goods": "нарушение срока передачи предварительно оплаченного товара неустойка",
    "delay_service": "нарушение сроков выполнения работ оказания услуг неустойка",
    "defect": "товар ненадлежащего качества недостатки требования потребителя",
    "refund_refusal": "отказ продавца вернуть деньги потребителю неустойка",
    "other": "нарушение прав потребителя",
}
INTENTS = {"new_case", "update", "question"}
TAG_FIND_RE = re.compile(r"\[((?:НОРМА|WEB)-\d+)\]")


def parse_json(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def ask_json(prompt, **variables) -> dict:
    return parse_json(chat(prompt, variables, json_mode=True, temperature=0.1))


def facts_summary(facts: dict | None) -> str:
    if not facts:
        return "—"

    def prune(value):
        if isinstance(value, dict):
            pruned = {k: prune(v) for k, v in value.items()}
            return {k: v for k, v in pruned.items() if v not in (None, [], {}, "")}
        return value

    return json.dumps(prune(facts), ensure_ascii=False, indent=1)


def extract_facts(story: str) -> CaseFacts:
    # превращаем неформальный текст в структурированную фабулу.
    return CaseFacts.model_validate(ask_json(EXTRACT_PROMPT, user_text=story))


def search_local(query: str) -> list[dict]:
    try:
        docs = get_local_retriever().invoke(query)
    except Exception as e:
        logging.warning(f"Локальный поиск недоступен: {e}")
        return []
    items = []
    for i, d in enumerate(docs, 1):
        source = d.metadata.get("source", "")
        title = d.metadata.get("title") or Path(source).stem or "локальный документ"
        article = d.metadata.get("article") or ""
        items.append({
            "tag": f"НОРМА-{i}",
            "title": f"{title}, {article}" if article else title,
            "file": Path(source).name if source else "",
            "url": None,
            "text": d.page_content,
        })
    return items


def search_web(query: str) -> list[dict]:
    if not WEB_SEARCH_ENABLED:
        return []
    return [
        {
            "tag": f"WEB-{i}",
            "title": r.get("title", ""),
            "file": "",
            "url": r.get("href"),
            "text": r.get("body", ""),
        }
        for i, r in enumerate(web_search(query), 1)
    ]


def format_norms(items: list[dict]) -> str:
    if not items:
        return "Норм не найдено."
    return "\n\n".join(f"[{n['tag']}] {n['title']}\n{n['text']}" for n in items)


def noise_names(items: list[dict]) -> list[str]:
    names = set()
    for n in items:
        if n["file"]:
            names.add(n["file"])
            names.add(Path(n["file"]).stem + ".pdf")
    return sorted(names, key=len, reverse=True)


def gather_norms(facts: CaseFacts) -> list[dict]:
    # собираем нормы из локальной базы и из интернета.
    topic = VIOLATION_QUERIES[facts.violation_type]
    local_query = " ".join(filter(None, [facts.subject, facts.violation_description, topic]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        local = pool.submit(search_local, local_query)
        web = pool.submit(search_web, f"закон о защите прав потребителей {topic}")
        return local.result() + web.result()


def compose(facts: CaseFacts, norms: list[dict]) -> Composed:
    data = ask_json(
        COMPOSE_PROMPT,
        facts=facts_summary(facts.model_dump(mode="json")),
        norms=format_norms(norms),
    )
    return Composed.model_validate(data)


def generate_case(story: str) -> dict:
    # Полный пайплайн.
    started = time.perf_counter()

    logging.info("Шаг 1: извлечение фактов")
    facts = extract_facts(story)

    logging.info("Шаг 2: сбор норм")
    norms = gather_norms(facts)

    logging.info("Шаг 3: составление текста")
    composed = compose(facts, norms)
    used = set(TAG_FIND_RE.findall(" ".join(composed.facts_text + composed.legal_text)))

    logging.info("Шаг 4 : рендер шаблона")
    context = build_context(facts, composed, noise_names(norms))
    isk = strip_markers(render_marked(context))
    logging.info(f"Иск готов за {time.perf_counter() - started:.1f} с")

    return {
        "story": story,
        "facts": facts.model_dump(mode="json"),
        "context": context,
        "isk": isk,
        "missing": find_missing(isk),
        "sources": [
            {"tag": n["tag"], "title": n["title"], "url": n["url"], "excerpt": n["text"][:400], "used": n["tag"] in used}
            for n in norms
        ],
    }


# быстрая классификации по длине и знаку вопроса, если не подходит, то общая классификация через llm
def quick_intent(message: str, has_case: bool) -> str | None:
    text = message.strip()
    is_question = text.endswith("?") and len(text) < 300
    if not has_case:
        return "question" if is_question and len(text) < 200 else "new_case"
    return "question" if is_question else None

# разделение запроса пользователя по намерению кейс или вопрос
def classify_intent(message: str, case: dict | None) -> str:
    quick = quick_intent(message, bool(case))
    if quick:
        return quick
    data = ask_json(
        INTENT_PROMPT,
        has_case="да" if case else "нет",
        facts=facts_summary(case.get("facts")) if case else "—",
        message=message,
    )
    intent = str(data.get("intent", "")).strip().lower()
    if intent not in INTENTS:
        intent = "question" if case else "new_case"
    if intent == "update" and not case:
        intent = "new_case"
    return intent


# последние HISTORY_TURNS реплик -> текст для промпта
def format_history(history: list[dict]) -> str:
    turns = history[-HISTORY_TURNS:]
    if not turns:
        return "—"
    names = {"user": "Пользователь", "assistant": "Ассистент"}
    return "\n".join(f"{names.get(t['role'], t['role'])}: {t['content'][:1500]}" for t in turns)


def answer_question(question: str, history: list[dict], case: dict | None) -> str:
    subject = ((case or {}).get("facts") or {}).get("subject") or ""
    norms = search_local(f"{question} {subject}".strip())
    answer = chat(ANSWER_PROMPT, {
        "facts": facts_summary(case.get("facts")) if case else "Иск ещё не составлен.",
        "isk": (case.get("isk") or "")[:6000] if case else "—",
        "norms": format_norms(norms),
        "history": format_history(history),
        "question": question,
    })
    return answer


def handle_chat(message: str, history: list[dict], case: dict | None, draft: dict | None = None, force: bool = False) -> dict:
    intent = classify_intent(message, case)
    logging.info(f"Намерение: {intent}")

    if intent == "new_case":
        return {"type": "isk", "updated": False, "case": generate_case(message)}
    if intent == "update":
        story = f"{case['story']}\n\nДополнение пользователя: {message}"
        return {"type": "isk", "updated": True, "case": generate_case(story)}
    return {"type": "answer", "answer": answer_question(message, history, case)}