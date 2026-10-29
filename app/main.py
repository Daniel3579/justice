import logging
from typing import Literal

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response
from jinja2 import TemplateError
from pydantic import BaseModel, Field

import storage
from config import MAX_MESSAGE_CHARS, MIN_PASSWORD_LENGTH
from generator import generate_case, handle_chat
from render import marked_to_docx, render_marked

logging.basicConfig(level=logging.INFO)

storage.init_db()

app = FastAPI(title="Генератор исков")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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
def generate(req: GenerateRequest):
    text = validate_text(req.text)
    if not text:
        return error(f"Поле 'text' обязательно (до {MAX_MESSAGE_CHARS} символов)", 400)
    try:
        return generate_case(text)
    except Exception as e:
        logging.exception("Ошибка генерации")
        return error(str(e), 500)


@app.post("/chat")
def chat(req: ChatRequest):
    message = validate_text(req.message)
    if not message:
        return error(f"Сообщение обязательно (до {MAX_MESSAGE_CHARS} символов)", 400)
    try:
        history = [t.model_dump() for t in req.history]
        return handle_chat(message, history, req.case, req.draft, req.force)
    except Exception as e:
        logging.exception("Ошибка чата")
        return error(str(e), 500)


@app.post("/export/docx")
def export_docx(req: ExportRequest):
    try:
        content = marked_to_docx(render_marked(req.context))
    except TemplateError as e:
        return error(f"Некорректные данные иска: {e}", 400)
    return Response(
        content=content,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": 'attachment; filename="iskovoe_zayavlenie.docx"'},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)