import pytest
from generator import extract_facts, generate_isk
from db import load_chroma_db
from retriever import get_local_retriever

# Маркер slow нужен, чтобы можно было запускать быстрые тесты отдельно:
# pytest tests/ -m "not slow"

@pytest.mark.slow
def test_extract_facts():
    """Проверяем, что LLM извлекает факты в заданном формате."""
    text = "Купил холодильник за 50000 руб, сломался через неделю. Магазин отказал."
    facts = extract_facts(text)
    
    # Проверяем строгую структуру, заданную в промпте EXTRACT_PROMPT
    assert "ИСТЕЦ:" in facts
    assert "ПРЕДМЕТ:" in facts
    assert "холодильник" in facts.lower()
    # Дополнительно проверяем, что модель вытащила цену
    assert "50000" in facts or "50 000" in facts


@pytest.mark.slow
def test_full_generation():
    """Проверяем полный пайплайн: от текста пользователя до готового иска."""
    user_text = "Купил телефон в магазине, через 2 месяца сломался."
    result = generate_isk(user_text)
    
    # 1. Проверяем, что вернулись все ключи
    assert "facts" in result
    assert "isk" in result
    assert "local_norms" in result
    assert "web_norms" in result
    
    isk_text = result["isk"]
    isk_upper = isk_text.upper()
    
    # 2. Проверяем, что иск не пустой и достаточно длинный
    assert len(isk_text) > 500, "Иск слишком короткий, вероятно, LLM не справилась."
    
    # 3. Проверяем СТРУКТУРУ документа
    assert "ИСТЕЦ" in isk_upper, "В иске отсутствует истец"
    assert "ОТВЕТЧИК" in isk_upper, "В иске отсутствует ответчик"
    
    # 4. Проверяем, что в иске фигурируют факты из запроса пользователя
    assert "ТЕЛЕФОН" in isk_upper, "В иске не упоминается предмет спора (телефон)"
    
    # 5. Проверяем, что есть просительная часть
    assert any(word in isk_upper for word in ["ПРОШУ", "ТРЕБОВАНИЯ", "ПРОСИТЕЛЬНАЯ"]), \
        "В иске отсутствует просительная часть"