import { useNavigate, useParams } from "react-router-dom";
import { useChats } from "../lib/ChatsContext";
import { CloseIcon, PanelIcon, PlusIcon } from "./Icons";
import { ProfileMenu } from "./ProfileMenu";

interface Props {
  collapsed: boolean;
  onCollapse: () => void;
  /** Закрывает панель после перехода (нужно на телефоне). */
  onNavigate: () => void;
}

export function Sidebar({ collapsed, onCollapse, onNavigate }: Props) {
  const { chats, deleteChat } = useChats();
  const { chatId } = useParams();
  const navigate = useNavigate();

  const go = (path: string) => {
    navigate(path);
    onNavigate();
  };

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="brand">
        <div className="logo">Justice</div>
        <button className="icon-btn" onClick={onCollapse} title="Скрыть панель">
          <PanelIcon />
        </button>
      </div>

      <button className="new-chat" onClick={() => go("/")}>
        <PlusIcon /> Новый чат
      </button>

      <div className="section-label">Чаты</div>
      <nav className="chats">
        {chats.length === 0 && <div className="empty-chats">Пока нет чатов</div>}
        {chats.map((c) => (
          <div
            key={c.id}
            role="button"
            tabIndex={0}
            className={`chat-item ${c.id === chatId ? "active" : ""}`}
            onClick={() => go(`/c/${c.id}`)}
            onKeyDown={(e) => e.key === "Enter" && go(`/c/${c.id}`)}
          >
            <span>{c.title}</span>
            <button
              className="del"
              title="Удалить"
              onClick={(e) => {
                e.stopPropagation();
                deleteChat(c.id);
                if (c.id === chatId) navigate("/");
              }}
            >
              <CloseIcon />
            </button>
          </div>
        ))}
      </nav>

      <ProfileMenu onNavigate={onNavigate} />
    </aside>
  );
}
