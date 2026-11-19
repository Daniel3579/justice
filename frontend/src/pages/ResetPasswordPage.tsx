import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { authApi } from "../api/auth";

const MIN_LENGTH = 6;

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < MIN_LENGTH) return setError(`Пароль должен быть не короче ${MIN_LENGTH} символов`);
    if (password !== repeat) return setError("Пароли не совпадают");
    setBusy(true);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сменить пароль");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-wrap">
        <div className="logo">Justice</div>
        <p className="tagline">Новый пароль</p>
        <div className="auth-card">
          {!token ? (
            <div className="auth-done">
              <p className="note err">Ссылка неполная. Откройте ссылку из письма целиком или запросите новую.</p>
              <Link className="submit as-link" to="/forgot">Запросить новую ссылку</Link>
            </div>
          ) : done ? (
            <div className="auth-done">
              <p>Пароль изменён. Войдите с новым паролем — на других устройствах сеансы завершены.</p>
              <Link className="submit as-link" to="/login">Войти</Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              <label className="field">
                Новый пароль
                <input
                  className="input"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              <label className="field">
                Повторите пароль
                <input
                  className="input"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={repeat}
                  onChange={(e) => setRepeat(e.target.value)}
                />
              </label>
              {error && (
                <div className="note err">
                  {error} {error.includes("устарела") && <Link className="link" to="/forgot">Запросить новую</Link>}
                </div>
              )}
              <button className="submit" type="submit" disabled={busy}>
                {busy ? "Сохраняем…" : "Сохранить пароль"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
