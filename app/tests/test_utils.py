# app/test_utils.py
from main import clean_text

def test_clean_text_removes_bold():
    assert clean_text("**Жирный текст**") == "Жирный текст"

def test_clean_text_removes_headers():
    assert clean_text("## Заголовок\nТекст") == "Заголовок\nТекст"

def test_clean_text_removes_extra_newlines():
    assert clean_text("Текст\n\n\n\nЕще текст") == "Текст\n\nЕще текст"