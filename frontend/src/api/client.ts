import { readJSON } from "../lib/storage";

export const TOKEN_KEY = "justice.token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Переводит частые технические ошибки бэкенда на понятный язык. */
function friendly(msg: string): string {
  const m = msg.toLowerCase();
  if (m.includes("11434") || (m.includes("connect") && m.includes("refused")) || m.includes("connecterror"))
    return "Не запущена Ollama. Запустите её (ollama serve) и повторите запрос.";
  if (m.includes("not found") && (m.includes("model") || m.includes("mistral") || m.includes("nomic")))
    return "Модель не скачана в Ollama. Выполните: ollama pull mistral и ollama pull nomic-embed-text.";
  return msg;
}

/** Достаёт понятный текст ошибки из ответа FastAPI ({detail} или {error}). */
async function errorMessage(r: Response): Promise<string> {
  const raw = await r.text().catch(() => "");
  try {
    const data = JSON.parse(raw);
    if (typeof data.detail === "string") return friendly(data.detail);
    if (Array.isArray(data.detail)) return data.detail.map((d: { msg?: string }) => d.msg).join("; ");
    if (typeof data.error === "string") return friendly(data.error);
  } catch {
    /* тело не JSON */
  }
  // Пустой ответ 500/502/504 — так dev-сервер Vite сообщает, что FastAPI на порту 8000 не отвечает.
  if (r.status >= 500 && !raw.trim())
    return "Бэкенд не отвечает. Запустите FastAPI (python main.py в папке app) на порту 8000.";
  if (r.status === 404) return "Адрес API не найден (404). Проверьте, что запущен нужный бэкенд.";
  return `Ошибка сервера (${r.status})`;
}

/** Запрос к API с токеном авторизации. */
export async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const token = readJSON<string | null>(TOKEN_KEY, null);
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let r: Response;
  try {
    r = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError("Сервер недоступен. Проверьте, что бэкенд запущен.", 0);
  }
  if (!r.ok) throw new ApiError(await errorMessage(r), r.status);
  return r;
}

export async function requestJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await request(path, init);
  return (await r.json()) as T;
}
