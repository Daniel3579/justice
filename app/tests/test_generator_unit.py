# app/tests/test_generator_unit.py
import pytest
from generator import (
    VIOLATION_QUERIES,
    facts_summary,
    format_norms,
    parse_json,
    quick_intent,
)


def test_violation_queries_have_all_types():
    from schemas import VIOLATION_TYPES
    assert VIOLATION_TYPES.issubset(VIOLATION_QUERIES.keys())


def test_parse_json_plain():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_inside_text():
    assert parse_json('Вот ответ: {"a": 2} конец') == {"a": 2}


def test_parse_json_broken():
    assert parse_json("не json") == {}


def test_parse_json_not_dict():
    assert parse_json("[1, 2, 3]") == {}


def test_facts_summary_prunes_empty():
    summary = facts_summary({"a": None, "b": "", "c": [], "d": {"x": None, "y": 5}})
    assert "a" not in summary
    assert "d" in summary
    assert "y" in summary


def test_facts_summary_none():
    assert facts_summary(None) == "—"


def test_format_norms_empty():
    assert format_norms([]) == "Норм не найдено."


def test_format_norms_ok():
    items = [{"tag": "НОРМА-1", "title": "Ст. 18", "text": "текст"}]
    out = format_norms(items)
    assert "[НОРМА-1] Ст. 18" in out
    assert "текст" in out


# --- быстрая классификация намерений ---

@pytest.mark.parametrize("message,has_case,expected", [
    ("Купил телефон, сломался", False, "new_case"),
    ("Что делать?", False, "question"),
    ("Что делать?", True, "question"),
    ("Добавьте адрес ответчика: Москва", True, None),  # нужен LLM
])
def test_quick_intent(message, has_case, expected):
    assert quick_intent(message, has_case) == expected