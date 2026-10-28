# app/test_generator_unit.py
from generator import _build_web_query

def test_build_web_query_keywords():
    facts = "ПРОСРОЧКА: 10 дней\nНедостатки: телефон сломан\nТребования: возврат"
    query = _build_web_query(facts)
    assert "защита прав потребителей иск" in query
    # Проверяем, что в запрос попали строки с ключевыми словами
    assert "просрочка" in query.lower() 
    assert "недостатки" in query.lower()