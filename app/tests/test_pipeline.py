# app/tests/test_pipeline.py
import pytest
from unittest.mock import patch

from generator import extract_facts, generate_case
from schemas import CaseFacts

# Запуск: pytest -m slow
pytestmark = pytest.mark.slow


# ---------- быстрая версия с моком LLM ----------

@patch("generator.chat")
def test_extract_facts_mocked(mock_chat):
    mock_chat.return_value = '''
    {
      "plaintiff": {"name": "Иван"},
      "defendant": {"name": "Магазин"},
      "subject": "холодильник",
      "price": 50000,
      "violation_type": "defect"
    }
    '''
    facts = extract_facts("Купил холодильник за 50000 руб, сломался.")
    assert isinstance(facts, CaseFacts)
    assert facts.plaintiff.name == "Иван"
    assert facts.price == 50000
    assert facts.violation_type == "defect"


@patch("generator.compose")
@patch("generator.gather_norms", return_value=[])
@patch("generator.extract_facts")
def test_generate_case_mocked(mock_extract, mock_norms, mock_compose):
    from schemas import Composed
    mock_extract.return_value = CaseFacts(
        subject="телефон",
        price=10000,
        violation_type="defect",
    )
    mock_compose.return_value = Composed(
        facts_text=["Истец купил телефон."],
        legal_text=["Согласно ст. 18 ЗПП."],
    )

    result = generate_case("Купил телефон, сломался.")

    assert set(result) >= {"story", "facts", "context", "isk", "missing", "sources"}
    assert "ИСКОВОЕ" in result["isk"].upper()
    # если шаблон требует полей — в missing они попадут
    assert isinstance(result["missing"], list)


