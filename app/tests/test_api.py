# app/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

# Мокаем пайплайн генерации, чтобы API-тесты были быстрыми
@pytest.fixture
def mock_generate_isk():
    with patch("main.generate_isk") as mock:
        mock.return_value = {
            "facts": "ИСТЕЦ: Иван\nОТВЕТЧИК: Магазин",
            "local_norms": "[НОРМА-1] Закон о защите прав",
            "web_norms": "[WEB-1] Судебная практика",
            "isk": "**ИСКОВОЕ ЗАЯВЛЕНИЕ**\nТекст иска..."
        }
        yield mock

def test_generate_json_success(mock_generate_isk):
    response = client.post("/generate", json={"text": "Я купил телефон..."})
    assert response.status_code == 200
    data = response.json()
    assert "facts" in data
    assert "isk" in data

def test_generate_json_empty_text():
    response = client.post("/generate", json={"text": "   "})
    assert response.status_code == 400
    assert response.json()["error"] == "Поле 'text' обязательно"

def test_generate_json_error(mock_generate_isk):
    mock_generate_isk.side_effect = Exception("Ошибка LLM")
    response = client.post("/generate", json={"text": "Текст"})
    assert response.status_code == 500
    assert "Ошибка LLM" in response.json()["error"]

def test_generate_docx_success(mock_generate_isk):
    response = client.post("/generate/docx", json={"text": "Текст"})
    assert response.status_code == 200
    # Проверяем заголовки, что это действительно файл docx
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "iskovoe_zayavlenie.docx" in response.headers["content-disposition"]

def test_generate_txt_success(mock_generate_isk):
    response = client.post("/generate/txt", json={"text": "Текст"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    # Проверяем, что markdown-звездочки очистились
    assert "**ИСКОВОЕ ЗАЯВЛЕНИЕ**" not in response.text
    assert "ИСКОВОЕ ЗАЯВЛЕНИЕ" in response.text