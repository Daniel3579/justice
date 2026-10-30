# app/tests/test_utils.py
from calc import fmt_date, money
from render import clean_paragraphs, short_name, strip_markers, strip_tags
from schemas import to_bool, to_date, to_number, to_str_list
from datetime import date
import pytest


# --- calc.money ---
def test_money_rounding():
    assert money(1234.567) == "1 234,57 руб."
    assert money(0) == "0,00 руб."
    assert money("1000") == "1 000,00 руб."


def test_fmt_date():
    assert fmt_date(date(2026, 1, 5)) == "05.01.2026"
    assert fmt_date(None) is None


# --- render ---
def test_strip_tags():
    assert strip_tags("Текст [НОРМА-1] и [WEB-2].") == "Текст и."
    assert strip_tags("Норма [НОРМА-1].") == "Норма."
    assert strip_tags("Без тегов.") == "Без тегов."


def test_strip_markers():
    marked = "[C]ЗАГОЛОВОК\n[R]Шапка\n[L]Текст"
    assert strip_markers(marked) == "ЗАГОЛОВОК\nШапка\nТекст"


def test_clean_paragraphs_filters_noise():
    items = ["Источник: law.pdf", "  кор ", "Нормальный абзац текста."]
    noise = ["law.pdf"]
    out = clean_paragraphs(items, noise)
    assert out == ["Нормальный абзац текста."]


def test_clean_paragraphs_removes_pdf_names():
    items = ["См. файл law.pdf для деталей, и ещё много текста."]
    out = clean_paragraphs(items, [])
    assert out == []


def test_short_name():
    assert short_name("Иванов Иван Иванович") == "Иванов И.И."
    assert short_name("Иван") == "Иван"
    assert short_name(None) is None


# --- schemas ---
@pytest.mark.parametrize("raw,expected", [
    ("1 500,50", 1500.5),
    ("2 тыс.", 2000.0),
    ("0", None),
    ("-100", 100.0),
    (None, None),
])
def test_to_number(raw, expected):
    assert to_number(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("01.02.2026", date(2026, 2, 1)),
    ("2026-02-01", date(2026, 2, 1)),
    ("мусор", None),
    (None, None),
])
def test_to_date(raw, expected):
    assert to_date(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("да", True), ("нет", False), ("true", True), ("?", None), (None, None),
])
def test_to_bool(raw, expected):
    assert to_bool(raw) == expected


def test_to_str_list():
    assert to_str_list("чек") == ["чек"]
    assert to_str_list(["a", None, " b "]) == ["a", "b"]
    assert to_str_list(None) == []