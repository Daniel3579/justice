import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../lib/theme";
import { Avatar } from "./Avatar";
import { LogoutIcon, MoonIcon, UserIcon } from "./Icons";

/** Иконка профиля в левом нижнем углу и всплывающее меню. */
export function ProfileMenu({ onNavigate }: { onNavigate: () => void }) {
  const { user, logout } = useAuth();
  const { toggle } = useTheme();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => ref.current && !ref.current.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  return (
    <div className="profile-wrap" ref={ref}>
      {open && (
        <div className="popover" role="dialog" aria-label="Аккаунт">
          <div className="pop-head">
            <Avatar email={user.email} size="lg" />
            <div style={{ minWidth: 0 }}>
              <div className="pop-title">Аккаунт</div>
              <div className="pop-mail">{user.email}</div>
            </div>
          </div>
          <button className="pop-row" onClick={() => { setOpen(false); navigate("/profile"); onNavigate(); }}>
            <UserIcon /> Профиль
          </button>
          <button className="pop-row" onClick={toggle}>
            <MoonIcon /> Сменить тему
          </button>
          <button className="pop-row" onClick={logout}>
            <LogoutIcon /> Выйти
          </button>
        </div>
      )}
      <button className="profile-btn" onClick={() => setOpen((o) => !o)} aria-haspopup="dialog" aria-expanded={open}>
        <Avatar email={user.email} />
        <div className="profile-email">{user.email}</div>
      </button>
    </div>
  );
}
