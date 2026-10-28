# app/test_web_search.py
from unittest.mock import patch, MagicMock
from web_search import format_web_results, web_search

def test_format_web_results_empty():
    assert format_web_results([]) == "Интернет-поиск не дал результатов."

def test_format_web_results_ok():
    results = [{"title": "Тайтл", "body": "Текст", "href": "http://url"}]
    formatted = format_web_results(results)
    assert "[WEB-1] Тайтл" in formatted
    assert "Текст" in formatted

@patch("web_search.DDGS")
def test_web_search_retry(mock_ddgs):
    # Эмулируем ошибку при первом вызове и успех при втором
    mock_instance = MagicMock()
    mock_instance.text.side_effect = [Exception("Error"), [{"title": "OK"}]]
    mock_ddgs.return_value.__enter__.return_value = mock_instance
    
    results = web_search("запрос", retries=1)
    assert len(results) == 1