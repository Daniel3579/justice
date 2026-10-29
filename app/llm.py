import logging
import re
import time

import httpx
from langchain_core.prompts import ChatPromptTemplate

from config import KEEP_ALIVE, LLM_MODEL, LLM_TIMEOUT, MAX_TOKENS_JSON, MAX_TOKENS_TEXT, NUM_CTX, OLLAMA_URL

ROLES = {"system": "system", "human": "user", "ai": "assistant"}
THINK_RE = re.compile(r"<think>.*?</think>", re.S)

_client = httpx.Client(timeout=httpx.Timeout(LLM_TIMEOUT, connect=10))
_supports_think = True

# Собирает сообщения из ChatPromptTemplate, переводя роли в формат олламы
# Отключает размышление
# Payload собирает
# Чистит ответ

class LLMError(RuntimeError):
    pass


def _messages(prompt: ChatPromptTemplate, variables: dict) -> list[dict]:
    return [{"role": ROLES.get(m.type, "user"), "content": m.content} for m in prompt.format_messages(**variables)]


def _post(payload: dict) -> httpx.Response:
    try:
        return _client.post(f"{OLLAMA_URL}/api/chat", json=payload)
    except httpx.TimeoutException as e:
        raise LLMError(f"Модель не ответила за {LLM_TIMEOUT} с. Попробуйте модель полегче или повторите запрос.") from e
    except httpx.ConnectError as e:
        raise LLMError("Нет связи с Ollama. Проверьте, что запущен ollama serve.") from e


def chat(prompt: ChatPromptTemplate, variables: dict, json_mode: bool = False,
         temperature: float = 0.2, max_tokens: int | None = None) -> str:
    global _supports_think

    payload = {
        "model": LLM_MODEL,
        "messages": _messages(prompt, variables),
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "options": {
            "temperature": temperature,
            "num_ctx": NUM_CTX,
            "num_predict": max_tokens or (MAX_TOKENS_JSON if json_mode else MAX_TOKENS_TEXT),
        },
    }
    if json_mode:
        payload["format"] = "json"
    if _supports_think:
        payload["think"] = False

    started = time.perf_counter()
    response = _post(payload)
    if response.status_code == 400 and "think" in response.text.lower():
        _supports_think = False
        payload.pop("think", None)
        response = _post(payload)
    if response.status_code != 200:
        raise LLMError(f"Ollama вернула ошибку {response.status_code}: {response.text[:300]}")

    data = response.json()
    content = THINK_RE.sub("", data.get("message", {}).get("content", "")).strip()
    logging.info(
        f"LLM: {time.perf_counter() - started:.1f} с, "
        f"промпт {data.get('prompt_eval_count', '?')} ток., ответ {data.get('eval_count', '?')} ток."
    )
    return content