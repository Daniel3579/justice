# app/tests/test_schemas.py
from datetime import date
import pytest
from schemas import CaseFacts, Composed, Plaintiff, Defendant


def test_plaintiff_from_string():
    p = Plaintiff.model_validate("Петров Пётр")
    assert p.name == "Петров Пётр"


def test_defendant_from_string():
    d = Defendant.model_validate("ООО Ромашка")
    assert d.name == "ООО Ромашка"


def test_case_facts_invalid_violation_falls_back_to_other():
    f = CaseFacts(violation_type="что-то")
    assert f.violation_type == "other"


def test_case_facts_empty_strings_cleaned():
    f = CaseFacts(court="", subject="null", violation_description="—")
    assert f.court is None
    assert f.subject is None
    assert f.violation_description is None


def test_case_facts_date_and_number_normalization():
    f = CaseFacts(
        contract_date="01.02.2026",
        price="1 500,50",
        claim_sent="да",
        documents="чек",
    )
    assert f.contract_date == date(2026, 2, 1)
    assert f.price == 1500.5
    assert f.claim_sent is True
    assert f.documents == ["чек"]


def test_composed_from_string():
    c = Composed.model_validate({"facts_text": "Абзац 1\n\nАбзац 2", "legal_text": "Один"})
    assert c.facts_text == ["Абзац 1", "Абзац 2"]
    assert c.legal_text == ["Один"]