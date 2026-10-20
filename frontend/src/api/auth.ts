import { ApiError, TOKEN_KEY, requestJSON, request } from "./client";
import { readJSON, writeJSON, remove } from "../lib/storage";

export interface User {
  email: string;
  created_at: string;
}

/**
 * Ожидаемые эндпоинты бэкенда:
 *   POST   /auth/register  {email, password}                    -> {access_token}
 *   POST   /auth/login     {email, password}                    -> {access_token}
 *   GET    /me                                                  -> {email, created_at}
 *   POST   /me/password    {current_password, new_password}     -> 204
 *   DELETE /me                                                  -> 204
 *
 * Пока их нет, VITE_MOCK_AUTH=true включает заглушку: аккаунты хранятся в браузере.
 * Заглушка только для разработки — пароли в ней не защищены.
 */
const MOCK = import.meta.env.VITE_MOCK_AUTH !== "false";

export const getToken = () => readJSON<string | null>(TOKEN_KEY, null);
const setToken = (t: string) => writeJSON(TOKEN_KEY, t);
export const clearToken = () => remove(TOKEN_KEY);

/* ---------- Настоящий API ---------- */
const real = {
  async login(email: string, password: string) {
    const { access_token } = await requestJSON<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(access_token);
  },
  async register(email: string, password: string) {
    const { access_token } = await requestJSON<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(access_token);
  },
  me: () => requestJSON<User>("/me"),
  async changePassword(current_password: string, new_password: string) {
    await request("/me/password", { method: "POST", body: JSON.stringify({ current_password, new_password }) });
  },
  async deleteAccount() {
    await request("/me", { method: "DELETE" });
  },
};

/* ---------- Заглушка ---------- */
const USERS_KEY = "justice.mock.users";
type MockUsers = Record<string, { password: string; created_at: string }>;
const users = () => readJSON<MockUsers>(USERS_KEY, {});
const delay = () => new Promise((r) => setTimeout(r, 300));

const mock = {
  async login(email: string, password: string) {
    await delay();
    const u = users()[email];
    if (!u || u.password !== password) throw new ApiError("Неверная почта или пароль", 401);
    setToken(email);
  },
  async register(email: string, password: string) {
    await delay();
    const all = users();
    if (all[email]) throw new ApiError("Аккаунт с такой почтой уже существует", 409);
    all[email] = { password, created_at: new Date().toISOString() };
    writeJSON(USERS_KEY, all);
    setToken(email);
  },
  async me(): Promise<User> {
    const email = getToken();
    const u = email ? users()[email] : undefined;
    if (!email || !u) throw new ApiError("Не авторизован", 401);
    return { email, created_at: u.created_at };
  },
  async changePassword(current: string, next: string) {
    await delay();
    const email = getToken()!;
    const all = users();
    if (all[email]?.password !== current) throw new ApiError("Текущий пароль указан неверно", 400);
    all[email].password = next;
    writeJSON(USERS_KEY, all);
  },
  async deleteAccount() {
    await delay();
    const all = users();
    delete all[getToken()!];
    writeJSON(USERS_KEY, all);
  },
};

export const authApi = MOCK ? mock : real;
