# Обновление Justice

## Что нового

1. Запросы не по теме. Сообщения, не связанные с юридической тематикой (погода, рецепты, программирование и т. п.), не обрабатываются. Пользователь видит красную карточку с пояснением.

2. Админ-панель. Доступна администраторам через меню профиля → «Администрирование» (адрес /admin-panel). В ней:
   - статистика: пользователи, чаты, составленные иски, ответы на вопросы, запросы не по теме, ошибки;
   - загрузка и удаление PDF с нормативными актами;
   - переиндексация базы документов.
   Подробно — в README_ADMIN.md.

3. Сброс пароля. На странице входа есть ссылка «Забыли пароль?». Пользователь получает на почту ссылку, действующую 60 минут. Если почта не настроена, ссылка пишется в лог backend.

4. Удаление аккаунта. Пользователь может удалить свой аккаунт вместе со всеми чатами.

5. Экспорт. Готовый иск можно скачать в форматах DOCX, PDF и Markdown.

6. База данных. SQLite заменена на PostgreSQL. Для просмотра базы добавлен Adminer (http://localhost:8081). Старые данные из SQLite не переносятся.

## Новые эндпоинты

- POST /auth/forgot — запросить ссылку для сброса пароля
- POST /auth/reset — задать новый пароль по ссылке
- DELETE /me — удалить аккаунт
- POST /export/{docx|pdf|md} — скачать иск
- GET /admin/stats — статистика
- GET /admin/documents — список документов
- POST /admin/documents — загрузить PDF
- DELETE /admin/documents/{name} — удалить PDF
- POST /admin/reindex — запустить переиндексацию
- GET /admin/reindex — статус переиндексации

Все /admin/* доступны только администраторам.

## Изменённые файлы

Backend (app/):
- новые: mailer.py, indexer.py
- изменены: main.py, storage.py, generator.py, prompts.py, render.py, retriever.py, config.py, requirements.txt, Dockerfile, test_api.py

Frontend (frontend/):
- новые: pages/AdminPage.tsx, pages/ForgotPasswordPage.tsx, pages/ResetPasswordPage.tsx, api/admin.ts, styles.additions.css
- изменены: App.tsx, api/auth.ts, api/client.ts, api/generate.ts, components/MessageView.tsx, components/ProfileMenu.tsx, components/Icons.tsx, lib/ChatsContext.tsx, pages/ChatPage.tsx, pages/LoginPage.tsx, nginx.conf, vite.config.ts

Корень проекта:
- изменён: docker-compose.yml (добавлены PostgreSQL и Adminer)
- новый: README_ADMIN.md

## Новые зависимости

- psycopg[binary] — драйвер PostgreSQL
- reportlab — генерация PDF

## Как запустить

Ollama должна быть запущена на компьютере.

    docker compose down
    docker compose up -d --build

Первый запуск занимает несколько минут: строится поисковый индекс. Пока он строится, сайт может отвечать ошибкой 502.

Адреса:
- сайт — http://localhost:8080
- Adminer — http://localhost:8081 (сервер db, логин, пароль и база — justice)
- PostgreSQL — localhost:5433

## Как стать администратором

Зарегистрируйтесь на сайте, затем в Adminer выполните:

    UPDATE users SET is_admin = TRUE WHERE email = 'ваша@почта';

и обновите страницу.

## Логи

    docker compose logs -f backend
