# Justice — фронтенд

React 19 + TypeScript + Vite. Экраны: вход и регистрация, чат с генерацией иска, профиль.

## Запуск

Нужен Node.js 18 или новее.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

FastAPI должен работать на `http://localhost:8000`. Vite сам перенаправляет на него запросы
`/generate`, `/auth`, `/me` (настройка в `vite.config.ts`), поэтому CORS не нужен.

## Авторизация

Пока в бэкенде нет аккаунтов, в `.env` стоит `VITE_MOCK_AUTH=true`: регистрация и вход
работают прямо в браузере (только для разработки, пароли не защищены).
Когда бэкенд будет готов, поставьте `VITE_MOCK_AUTH=false`. Фронт ждёт такие эндпоинты:

| Метод  | Путь             | Тело                                   | Ответ                    |
|--------|------------------|----------------------------------------|--------------------------|
| POST   | `/auth/register` | `{email, password}`                    | `{access_token}`         |
| POST   | `/auth/login`    | `{email, password}`                    | `{access_token}`         |
| GET    | `/me`            | —                                      | `{email, created_at}`    |
| POST   | `/me/password`   | `{current_password, new_password}`     | 204                      |
| DELETE | `/me`            | —                                      | 204                      |

Токен передаётся в заголовке `Authorization: Bearer <token>`. Ошибки — в формате FastAPI
(`{"detail": "текст"}`), текст показывается пользователю как есть.

## Сборка для продакшена

```bash
npm run build        # результат в frontend/dist
```

Чтобы FastAPI отдавал собранный фронт, добавьте в конец `app/main.py`
(перед `if __name__ == "__main__"`):

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

@app.get("/{path:path}", include_in_schema=False)
async def spa(path: str):
    # все неизвестные пути отдаём index.html — маршрутами занимается React
    return FileResponse(os.path.join(DIST, "index.html"))
```

Этот обработчик должен идти **после** всех API-эндпоинтов.

## Структура

```
src/
  api/          запросы к бэкенду (client, auth, generate)
  auth/         контекст текущего пользователя
  components/   сайдбар, меню профиля, строка ввода, сообщения, иконки
  lib/          история чатов, тема, утилиты
  pages/        LoginPage, ChatPage, ProfilePage
  styles.css    все стили (цвета светлой и тёмной темы — в начале файла)
```

История чатов сейчас хранится в браузере, отдельно для каждого пользователя
(`src/lib/ChatsContext.tsx`). Когда на бэкенде появится `/chats`, менять нужно только этот файл.
