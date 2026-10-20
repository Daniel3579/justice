import { useState, type FormEvent } from "react";
import { authApi } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import { Avatar } from "../components/Avatar";
import { useChats } from "../lib/ChatsContext";
import { formatDate, pluralChats } from "../lib/format";
import { useTheme, type Theme } from "../lib/theme";

const THEMES: { value: Theme; label: string }[] = [
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
  { value: "auto", label: "Системная" },
];

export function ProfilePage() {
  const { user, logout, deleteAccount } = useAuth();
  const { chats, clearAll } = useChats();
  const { theme, setTheme } = useTheme();
  if (!user) return null;

  const created = formatDate(user.created_at);

  return (
    <div className="stage">
      <div className="page">
        <h2>Профиль</h2>

        <div className="profile-hero">
          <Avatar email={user.email} size="xl" />
          <div>
            <div className="k" style={{ fontWeight: 600 }}>{user.email}</div>
            {created && <div className="v">Аккаунт создан {created}</div>}
          </div>
        </div>

        <div className="card-title">Аккаунт</div>
        <div className="card">
          <div className="row">
            <div><div className="k">Почта</div><div className="v">{user.email}</div></div>
          </div>
          <PasswordRow />
        </div>

        <div className="card-title">Оформление</div>
        <div className="card">
          <div className="row">
            <div className="k">Тема</div>
            <div className="seg">
              {THEMES.map((t) => (
                <button key={t.value} className={theme === t.value ? "on" : ""} onClick={() => setTheme(t.value)}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="card-title">Данные</div>
        <div className="card">
          <div className="row">
            <div><div className="k">История чатов</div><div className="v">{chats.length} {pluralChats(chats.length)}</div></div>
            <button className="btn" disabled={!chats.length} onClick={() => confirm("Удалить все чаты?") && clearAll()}>
              Очистить
            </button>
          </div>
          <div className="row">
            <div className="k">Выйти из аккаунта</div>
            <button className="btn" onClick={logout}>Выйти</button>
          </div>
          <div className="row">
            <div className="k">Удалить аккаунт</div>
            <button
              className="btn danger"
              onClick={() => confirm("Удалить аккаунт без возможности восстановления?") && deleteAccount().catch((e) => alert(e.message))}
            >
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function PasswordRow() {
  const [open, setOpen] = useState(false);
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [next2, setNext2] = useState("");
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (next.length < 8) return setNote({ ok: false, text: "Новый пароль должен быть не короче 8 символов" });
    if (next !== next2) return setNote({ ok: false, text: "Пароли не совпадают" });
    setBusy(true);
    try {
      await authApi.changePassword(cur, next);
      setNote({ ok: true, text: "Пароль изменён" });
      setCur(""); setNext(""); setNext2("");
      setTimeout(() => { setOpen(false); setNote(null); }, 1200);
    } catch (err) {
      setNote({ ok: false, text: err instanceof Error ? err.message : "Не удалось сменить пароль" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="row">
        <div><div className="k">Пароль</div><div className="v">••••••••</div></div>
        <button className="btn" onClick={() => { setOpen((o) => !o); setNote(null); }}>
          {open ? "Отмена" : "Сменить"}
        </button>
      </div>
      {open && (
        <form className="inline-form" onSubmit={submit}>
          <input className="input" type="password" placeholder="Текущий пароль" autoComplete="current-password" value={cur} onChange={(e) => setCur(e.target.value)} />
          <input className="input" type="password" placeholder="Новый пароль" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} />
          <input className="input" type="password" placeholder="Повторите новый пароль" autoComplete="new-password" value={next2} onChange={(e) => setNext2(e.target.value)} />
          {note && <div className={`note ${note.ok ? "ok" : "err"}`}>{note.text}</div>}
          <button className="btn primary" disabled={busy}>{busy ? "Сохраняю…" : "Сохранить"}</button>
        </form>
      )}
    </>
  );
}
