import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { authApi } from "../api/auth";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await authApi.forgotPassword(email.trim());
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить письмо");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-wrap">
        <div className="logo">Justice</div>
        <p className="tagline">Восстановление пароля</p>
        <div className="auth-card">
          {sent ? (
            <div className="auth-done">
              <p>
                Если аккаунт с почтой <b>{email.trim()}</b> существует, мы отправили на неё ссылку для сброса пароля.
                Ссылка действует 60 минут.
              </p>
              <p className="note">Письма нет? Проверьте папку «Спам» или запросите ссылку повторно через минуту.</p>
              <Link className="submit as-link" to="/login">Вернуться ко входу</Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              <label className="field">
                Почта
                <input
                  className="input"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              {error && <div className="note err">{error}</div>}
              <button className="submit" type="submit" disabled={busy || !email.trim()}>
                {busy ? "Отправляем…" : "Отправить ссылку"}
              </button>
            </form>
          )}
        </div>
        <p className="terms">
          <Link className="link" to="/login">Вспомнили пароль? Войти</Link>
        </p>
      </div>
    </div>
  );
}
