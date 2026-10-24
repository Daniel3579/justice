import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { fetchChats, removeChat, saveChat } from "../api/chats";
import type { CaseState } from "../api/generate";

export type Message =
  | { role: "user"; text: string }
  | { role: "pending" }
  | { role: "error"; text: string }
  | {
      role: "assistant";
      kind?: "isk" | "answer";
      text: string;
      case?: CaseState;
      updated?: boolean;
      source?: string;
    };

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

interface ChatsState {
  chats: Chat[];
  getChat: (id?: string) => Chat | undefined;
  createChat: (firstMessage: string) => Chat;
  updateChat: (id: string, update: (chat: Chat) => Chat) => void;
  deleteChat: (id: string) => void;
}

const ChatsContext = createContext<ChatsState | null>(null);

function makeTitle(text: string): string {
  const t = text.replace(/\s+/g, " ").trim();
  return t.length > 60 ? t.slice(0, 57) + "…" : t || "Новый чат";
}

function newId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function ChatsProvider({ userKey, children }: { userKey: string; children: ReactNode }) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  const chatsRef = useRef<Chat[]>([]);
  const queue = useRef(new Map<string, Promise<void>>());

  const commit = (next: Chat[]) => {
    chatsRef.current = next;
    setChats(next);
  };

  useEffect(() => {
    let alive = true;
    setStatus("loading");
    fetchChats()
      .then((list) => {
        if (!alive) return;
        commit(list);
        setStatus("ready");
      })
      .catch((e) => {
        console.error("Не удалось загрузить чаты", e);
        if (alive) setStatus("error");
      });
    return () => {
      alive = false;
    };
  }, [userKey, attempt]);

  const enqueue = (id: string, task: () => Promise<void>) => {
    const prev = queue.current.get(id) ?? Promise.resolve();
    const next = prev.then(task).catch((e) => console.error("Не удалось сохранить чат", e));
    queue.current.set(id, next);
  };

  const value = useMemo<ChatsState>(
    () => ({
      chats,
      getChat: (id) => (id ? chats.find((c) => c.id === id) : undefined),
      createChat: (firstMessage) => {
        const chat: Chat = { id: newId(), title: makeTitle(firstMessage), messages: [], updatedAt: Date.now() };
        commit([chat, ...chatsRef.current]);
        return chat;
      },
      updateChat: (id, update) => {
        const current = chatsRef.current.find((c) => c.id === id);
        if (!current) return;
        const next = { ...update(current), updatedAt: Date.now() };
        commit([next, ...chatsRef.current.filter((c) => c.id !== id)]);
        enqueue(id, () => saveChat(next));
      },
      deleteChat: (id) => {
        commit(chatsRef.current.filter((c) => c.id !== id));
        enqueue(id, () => removeChat(id));
      },
    }),
    [chats],
  );

  if (status === "loading") return null;

  if (status === "error") {
    return (
      <div className="stage">
        <div className="home">
          <div className="error-box">Не удалось загрузить чаты. Проверьте, что бэкенд запущен.</div>
          <button className="chip" onClick={() => setAttempt((a) => a + 1)}>Повторить</button>
        </div>
      </div>
    );
  }

  return <ChatsContext.Provider value={value}>{children}</ChatsContext.Provider>;
}

export function useChats(): ChatsState {
  const ctx = useContext(ChatsContext);
  if (!ctx) throw new Error("useChats должен использоваться внутри ChatsProvider");
  return ctx;
}