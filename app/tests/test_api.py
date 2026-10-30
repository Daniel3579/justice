# app/tests/test_api.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import date
from render import build_context
from schemas import CaseFacts, Composed

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Изолированная БД для каждого теста."""
    import config
    monkeypatch.setattr(config, "APP_DB_PATH", tmp_path / "app.db")

    # важно: импорт после подмены пути
    import importlib
    import storage
    importlib.reload(storage)

    import main
    importlib.reload(main)
    return TestClient(main.app)


@pytest.fixture
def fake_case():
    return {
        "story": "Я купил телефон...",
        "facts": {
            "plaintiff": {"name": "Иван"},
            "defendant": {"name": "Магазин"},
            "subject": "телефон",
            "violation_type": "defect",
        },
        "context": {},
        "isk": "ИСКОВОЕ ЗАЯВЛЕНИЕ\nТекст",
        "missing": [],
        "sources": [],
    }


# ---------- /generate ----------

def test_generate_success(client, fake_case):
    with patch("main.generate_case", return_value=fake_case) as m:
        r = client.post("/generate", json={"text": "Купил телефон"})
    assert r.status_code == 200
    assert "isk" in r.json()
    m.assert_called_once()


def test_generate_empty_text(client):
    r = client.post("/generate", json={"text": "   "})
    assert r.status_code == 400
    assert "обязательно" in r.json()["error"]


def test_generate_too_long_text(client):
    r = client.post("/generate", json={"text": "а" * 9000})
    assert r.status_code == 400


def test_generate_llm_error(client):
    with patch("main.generate_case", side_effect=RuntimeError("LLM упала")):
        r = client.post("/generate", json={"text": "Текст"})
    assert r.status_code == 500
    assert "LLM упала" in r.json()["error"]


# ---------- /export/docx ----------

def test_export_docx_success(client):
    facts = CaseFacts(
        plaintiff={"name": "Иванов Иван"},
        defendant={"name": "ООО Магазин"},
        subject="телефон",
        price=50_000,
        paid_amount=50_000,
        violation_type="defect",
        claim_date=date(2026, 4, 1),
        moral_damage=10_000,
    )
    context = build_context(facts, Composed(facts_text=["Текст."], legal_text=["Норма."]),
                            today=date(2026, 6, 1))
    r = client.post("/export/docx", json={"context": context})
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


# ---------- /chat ----------

def test_chat_empty_message(client):
    r = client.post("/chat", json={"message": "  "})
    assert r.status_code == 400


def test_chat_delegates_to_handler(client):
    with patch("main.handle_chat", return_value={"type": "answer", "answer": "ok"}) as m:
        r = client.post("/chat", json={"message": "Куда подавать?"})
    assert r.status_code == 200
    assert r.json() == {"type": "answer", "answer": "ok"}
    m.assert_called_once()


# ---------- auth ----------

def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@b.ru", "password": "secret1"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = client.post("/auth/login", json={"email": "a@b.ru", "password": "secret1"})
    assert r2.status_code == 200

    r3 = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == "a@b.ru"


def test_register_duplicate(client):
    client.post("/auth/register", json={"email": "a@b.ru", "password": "secret1"})
    r = client.post("/auth/register", json={"email": "a@b.ru", "password": "secret1"})
    assert r.status_code == 409


def test_register_short_password(client):
    r = client.post("/auth/register", json={"email": "a@b.ru", "password": "123"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.ru", "password": "secret1"})
    r = client.post("/auth/login", json={"email": "a@b.ru", "password": "wrong!!"})
    assert r.status_code == 401


def test_me_unauthorized(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer nope"}).status_code == 401