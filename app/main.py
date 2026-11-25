import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from jinja2 import TemplateError
from pydantic import BaseModel, Field

import indexer
import storage
from config import APP_URL, DOCUMENTS_PATH, MAX_MESSAGE_CHARS, MAX_UPLOAD_MB, MIN_PASSWORD_LENGTH
from generator import generate_case, handle_chat
from mailer import send_reset_email
from render import marked_to_docx, marked_to_markdown, marked_to_pdf, render_marked

logging.basicConfig(level=logging.INFO)

storage.init_db()

app = FastAPI(title="Генератор исков")

EXPORTS = {
    "docx": (marked_to_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "pdf": (marked_to_pdf, "application/pdf"),
    "md": (lambda marked: marked_to_markdown(marked).encode("utf-8"), "text/markdown; charset=utf-8"),
}


class GenerateRequest(BaseModel):
    text: str


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(default_factory=list)
    case: dict | None = None
    draft: dict | None = None
    force: bool = False


class ExportRequest(BaseModel):
    context: dict


class Credentials(BaseModel):
    email: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    token: str
    new_password: str


class ChatSave(BaseModel):
    title: str = Field(max_length=200)
    messages: list[dict]


def error(message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def validate_text(text: str) -> str | None:
    text = text.strip()
    if not text or len(text) > MAX_MESSAGE_CHARS:
        return None
    return text


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or len(email) > 254:
        raise HTTPException(400, "Укажите корректную почту")
    return email


def check_new_password(password: str):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")


def current_user(authorization: str | None = Header(default=None)) -> dict:
    token = (authorization or "").removeprefix("Bearer ").strip()
    user = storage.user_by_token(token) if token else None
    if not user:
        raise HTTPException(401, "Не авторизован")
    return user


def admin_user(user: dict = Depends(current_user)) -> dict:
    if not user["is_admin"]:
        raise HTTPException(403, "Доступ только для администраторов")
    return user


def document_path(name: str) -> Path:
    clean = Path(name).name
    if not clean or clean != name or not clean.lower().endswith(".pdf"):
        raise HTTPException(400, "Некорректное имя файла: нужен .pdf без папок в имени")
    return DOCUMENTS_PATH / clean


@app.post("/auth/register")
def register(body: Credentials):
    email = normalize_email(body.email)
    check_new_password(body.password)
    if not storage.create_user(email, body.password):
        raise HTTPException(409, "Аккаунт с такой почтой уже существует")
    return {"access_token": storage.create_session(email)}


@app.post("/auth/login")
def login(body: Credentials):
    email = normalize_email(body.email)
    if not storage.check_password(email, body.password):
        raise HTTPException(401, "Неверная почта или пароль")
    return {"access_token": storage.create_session(email)}


@app.post("/auth/forgot", status_code=204)
def forgot_password(body: ForgotRequest, background: BackgroundTasks):
    email = normalize_email(body.email)
    token = storage.create_password_reset(email)
    if token:
        background.add_task(send_reset_email, email, f"{APP_URL}/reset?token={token}")


@app.post("/auth/reset", status_code=204)
def reset_password(body: ResetRequest):
    check_new_password(body.new_password)
    if not storage.reset_password(body.token, body.new_password):
        raise HTTPException(400, "Ссылка для сброса пароля недействительна или устарела. Запросите новую.")


@app.get("/me")
def me(user: dict = Depends(current_user)):
    return user


@app.post("/me/password", status_code=204)
def change_password(body: PasswordChange, user: dict = Depends(current_user)):
    if not storage.check_password(user["email"], body.current_password):
        raise HTTPException(400, "Текущий пароль указан неверно")
    check_new_password(body.new_password)
    storage.set_password(user["email"], body.new_password)


@app.delete("/me", status_code=204)
def delete_me(user: dict = Depends(current_user)):
    storage.delete_user(user["email"])


@app.get("/chats")
def get_chats(user: dict = Depends(current_user)):
    return storage.list_chats(user["email"])


@app.put("/chats/{chat_id}", status_code=204)
def put_chat(chat_id: str, body: ChatSave, user: dict = Depends(current_user)):
    storage.save_chat(user["email"], chat_id, body.title, body.messages)


@app.delete("/chats/{chat_id}", status_code=204)
def remove_chat(chat_id: str, user: dict = Depends(current_user)):
    storage.delete_chat(user["email"], chat_id)


@app.post("/generate")
def generate(req: GenerateRequest, user: dict = Depends(current_user)):
    text = validate_text(req.text)
    if not text:
        return error(f"Поле 'text' обязательно (до {MAX_MESSAGE_CHARS} символов)", 400)
    try:
        result = generate_case(text)
        storage.log_event("isk")
        return result
    except Exception as e:
        logging.exception("Ошибка генерации")
        storage.log_event("error")
        return error(str(e), 500)


@app.post("/chat")
def chat(req: ChatRequest, user: dict = Depends(current_user)):
    message = validate_text(req.message)
    if not message:
        return error(f"Сообщение обязательно (до {MAX_MESSAGE_CHARS} символов)", 400)
    try:
        history = [t.model_dump() for t in req.history]
        result = handle_chat(message, history, req.case, req.draft, req.force)
    except Exception as e:
        logging.exception("Ошибка чата")
        storage.log_event("error")
        return error(str(e), 500)

    if result["type"] == "isk":
        storage.log_event("isk_update" if result.get("updated") else "isk")
    else:
        storage.log_event(result["type"])
    return result


@app.post("/export/{fmt}")
def export(fmt: Literal["docx", "pdf", "md"], req: ExportRequest, user: dict = Depends(current_user)):
    convert, media_type = EXPORTS[fmt]
    try:
        content = convert(render_marked(req.context))
    except TemplateError as e:
        return error(f"Некорректные данные иска: {e}", 400)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="iskovoe_zayavlenie.{fmt}"'},
    )


@app.get("/admin/stats")
def admin_stats(user: dict = Depends(admin_user)):
    return storage.stats()


@app.get("/admin/documents")
def admin_documents(user: dict = Depends(admin_user)):
    files = sorted(DOCUMENTS_PATH.glob("*.pdf")) if DOCUMENTS_PATH.exists() else []
    return {
        "documents": [
            {
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
            }
            for f in files
        ],
        "index": indexer.status(),
    }


@app.post("/admin/documents", status_code=201)
def admin_upload(files: list[UploadFile] = File(...), user: dict = Depends(admin_user)):
    DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
    saved = []
    for upload in files:
        path = document_path(upload.filename or "")
        data = upload.file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Файл {path.name} больше {MAX_UPLOAD_MB} МБ")
        if not data.startswith(b"%PDF"):
            raise HTTPException(400, f"Файл {path.name} не похож на PDF")
        path.write_bytes(data)
        saved.append(path.name)
    return {"saved": saved}


@app.delete("/admin/documents/{name}", status_code=204)
def admin_delete_document(name: str, user: dict = Depends(admin_user)):
    path = document_path(name)
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    path.unlink()


@app.post("/admin/reindex", status_code=202)
def admin_reindex(user: dict = Depends(admin_user)):
    if not indexer.start():
        raise HTTPException(409, "Переиндексация уже выполняется")
    return indexer.status()


@app.get("/admin/reindex")
def admin_reindex_status(user: dict = Depends(admin_user)):
    return indexer.status()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
