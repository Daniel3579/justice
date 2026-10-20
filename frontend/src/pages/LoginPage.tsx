import { useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";

type Mode = "login" | "register";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const switchMode = (m: Mode) => {
    setMode(m);
    setError("");
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const mail = email.trim().toLowerCase();
    if (!/^\S+@\S+\.\S+$/.test(mail)) return setError("Введите корректную почту");
    if (pw.length < 8) return setError("Пароль должен быть не короче 8 символов");
    if (mode === "register" && pw !== pw2) return setError("Пароли не совпадают");

    setBusy(true);
    setError("");
    try {
      await (mode === "login" ? login(mail, pw) : register(mail, pw));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так");
      setBusy(false);
    }
  };

  return (
    <div className="auth">
      <div className="auth-wrap">
        <div className="logo">Justice</div>
        <p className="tagline">Исковые заявления по защите прав потребителей — из обычного описания ситуации</p>

        <div className="auth-card">
          <div className="tabs">
            <button className={mode === "login" ? "on" : ""} onClick={() => switchMode("login")}>Вход</button>
            <button className={mode === "register" ? "on" : ""} onClick={() => switchMode("register")}>Регистрация</button>
          </div>

          <form onSubmit={submit} noValidate>
            <label className="field">
              Почта
              <input className="input" type="email" placeholder="you@example.com" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="field">
              <span className="field-row">
                <span>Пароль</span>
                {mode === "login" && (
                  <a href="#" className="link" onClick={(e) => { e.preventDefault(); alert("Восстановление пароля появится, когда будет готов бэкенд"); }}>
                    Забыли пароль?
                  </a>
                )}
              </span>
              <input
                className="input"
                type="password"
                placeholder="Не менее 8 символов"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={pw}
                onChange={(e) => setPw(e.target.value)}
              />
            </label>
            {mode === "register" && (
              <label className="field">
                Повторите пароль
                <input className="input" type="password" placeholder="Ещё раз" autoComplete="new-password" value={pw2} onChange={(e) => setPw2(e.target.value)} />
              </label>
            )}
            {error && <div className="note err">{error}</div>}
            <button className="submit" type="submit" disabled={busy}>
              {busy ? "Подождите…" : mode === "login" ? "Войти" : "Создать аккаунт"}
            </button>
          </form>

          {mode === "register" && (
            <p className="terms">Регистрируясь, вы соглашаетесь с условиями использования и обработкой персональных данных.</p>
          )}
        </div>
      </div>
    </div>
  );
}
