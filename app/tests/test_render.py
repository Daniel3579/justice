# app/tests/test_render.py
import io
from datetime import date
from unittest.mock import patch
from render import render_marked, strip_markers
from docx import Document

from render import (
    build_attachments,
    build_context,
    build_demands,
    describe_contract,
    find_missing,
    marked_to_docx,
    render_marked,
)
from schemas import CaseFacts, Composed


def make_facts(**kw):
    base = dict(
        plaintiff={"name": "Иванов Иван"},
        defendant={"name": "ООО Магазин"},
        subject="телефон",
        price=50_000,
        paid_amount=50_000,
        violation_type="defect",
        claim_date=date(2026, 4, 1),
        moral_damage=10_000,
    )
    base.update(kw)
    return CaseFacts(**base)


def test_describe_contract():
    f = CaseFacts(contract_number="A-1", contract_date=date(2026, 1, 1))
    assert describe_contract(f) == "№ A-1 от 01.01.2026"
    assert describe_contract(CaseFacts()) is None


def test_build_demands_includes_refund_and_penalty():
    facts = make_facts()
    composed = Composed()
    ctx = build_context(facts, composed, today=date(2026, 6, 1))
    demands = "\n".join(ctx["demands"])
    assert "Взыскать" in demands
    assert "неустойку" in demands
    assert "морального вреда" in demands
    assert "штраф" in demands


def test_build_demands_without_price_has_placeholder():
    facts = make_facts(price=None, paid_amount=None)
    composed = Composed()
    ctx = build_context(facts, composed, today=date(2026, 6, 1))
    assert any("[ТРЕБУЕТСЯ УТОЧНЕНИЕ" in d for d in ctx["demands"])


def test_build_attachments_deduplicates():
    facts = make_facts(documents=["Копия чека", "Копия чека"])
    items = build_attachments(facts)
    lowered = [i.lower() for i in items]
    assert len(lowered) == len(set(lowered))


def test_build_context_duty_exempt_small_claim():
    facts = make_facts(price=10_000, paid_amount=10_000)
    ctx = build_context(facts, Composed(), today=date(2026, 6, 1))
    assert ctx["duty_exempt"] is True


def test_build_context_duty_not_exempt_big_claim():
    facts = make_facts(price=2_000_000, paid_amount=2_000_000)
    ctx = build_context(facts, Composed(), today=date(2026, 6, 1))
    assert ctx["duty_exempt"] is False


def test_find_missing():
    text = "Тут [ТРЕБУЕТСЯ УТОЧНЕНИЕ: сумма] и [ТРЕБУЕТСЯ УТОЧНЕНИЕ: сумма]."
    assert find_missing(text) == ["сумма"]


def test_render_and_strip_markers():
    facts = make_facts()
    ctx = build_context(facts, Composed(facts_text=["Текст."], legal_text=["Норма."]),
                        today=date(2026, 6, 1))

    marked = render_marked(ctx)
    # в сыром виде маркеры ЕСТЬ — это и есть контракт
    assert "[C]" in marked

    plain = strip_markers(marked)
    assert "[C]" not in plain
    assert "[L]" not in plain
    assert "[R]" not in plain
    assert "ИСКОВОЕ" in plain.upper()


def test_marked_to_docx_returns_valid_file():
    raw = marked_to_docx("[C]ЗАГОЛОВОК\n[L]Текст иска.")
    assert raw[:2] == b"PK"
    doc = Document(io.BytesIO(raw))
    assert any("ЗАГОЛОВОК" in p.text for p in doc.paragraphs)