# app/tests/test_storage.py
import pytest


@pytest.fixture
def db(tmp_path, monkeypatch):
    import config, storage
    monkeypatch.setattr(config, "APP_DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(storage, "APP_DB_PATH", tmp_path / "t.db")
    storage.init_db()
    return storage


def test_create_and_check_password(db):
    assert db.create_user("a@b.ru", "secret1") is True
    assert db.check_password("a@b.ru", "secret1") is True
    assert db.check_password("a@b.ru", "wrong") is False


def test_duplicate_user(db):
    db.create_user("a@b.ru", "secret1")
    assert db.create_user("a@b.ru", "secret1") is False


def test_session_roundtrip(db):
    db.create_user("a@b.ru", "secret1")
    token = db.create_session("a@b.ru")
    assert db.user_by_token(token)["email"] == "a@b.ru"
    assert db.user_by_token("nope") is None


def test_set_password(db):
    db.create_user("a@b.ru", "secret1")
    db.set_password("a@b.ru", "newpass1")
    assert db.check_password("a@b.ru", "newpass1") is True
    assert db.check_password("a@b.ru", "secret1") is False


def test_chats_crud(db):
    db.create_user("a@b.ru", "secret1")
    db.save_chat("a@b.ru", "c1", "Заголовок", [{"role": "user", "content": "hi"}])
    chats = db.list_chats("a@b.ru")
    assert len(chats) == 1
    assert chats[0]["title"] == "Заголовок"

    db.save_chat("a@b.ru", "c1", "Новый", [])
    chats = db.list_chats("a@b.ru")
    assert chats[0]["title"] == "Новый"

    db.delete_chat("a@b.ru", "c1")
    assert db.list_chats("a@b.ru") == []


def test_delete_user_cascades(db):
    db.create_user("a@b.ru", "secret1")
    db.create_session("a@b.ru")
    db.save_chat("a@b.ru", "c1", "t", [])
    db.delete_user("a@b.ru")
    assert db.list_chats("a@b.ru") == []