import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { readJSON, writeJSON } from "./storage";

export type Message =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string; source: string }
  | { role: "error"; text: string }
  | { role: "pending" };

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
}

interface ChatsState {
  chats: Chat[];
  getChat: (id: string | undefined) => Chat | undefined;
  createChat: (firstMessage: string) => Chat;
  updateChat: (id: string, fn: (c: Chat) => Chat) => void;
  deleteChat: (id: string) => void;
  clearAll: () => void;
}

const ChatsContext = createContext<ChatsState | null>(null);

/**
 * История чатов. Пока хранится в браузере, отдельно для каждого пользователя.
 * Когда на бэкенде появится /chats, менять нужно только этот файл.
 */
export function ChatsProvider({ userKey, children }: { userKey: string; children: ReactNode }) {
  const storeKey = `justice.chats.${userKey}`;
  const [chats, setChats] = useState<Chat[]>(() =>
    // незавершённые запросы после перезагрузки страницы убираем
    readJSON<Chat[]>(storeKey, []).map((c) => ({ ...c, messages: c.messages.filter((m) => m.role !== "pending") })),
  );

  useEffect(() => writeJSON(storeKey, chats), [storeKey, chats]);

  const getChat = useCallback((id: string | undefined) => chats.find((c) => c.id === id), [chats]);

  const createChat = useCallback((firstMessage: string) => {
    const chat: Chat = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title: firstMessage.replace(/\s+/g, " ").slice(0, 60),
      messages: [],
      createdAt: Date.now(),
    };
    setChats((cs) => [chat, ...cs]);
    return chat;
  }, []);

  const updateChat = useCallback((id: string, fn: (c: Chat) => Chat) => {
    setChats((cs) => cs.map((c) => (c.id === id ? fn(c) : c)));
  }, []);

  const deleteChat = useCallback((id: string) => setChats((cs) => cs.filter((c) => c.id !== id)), []);
  const clearAll = useCallback(() => setChats([]), []);

  return (
    <ChatsContext.Provider value={{ chats, getChat, createChat, updateChat, deleteChat, clearAll }}>
      {children}
    </ChatsContext.Provider>
  );
}

export function useChats(): ChatsState {
  const ctx = useContext(ChatsContext);
  if (!ctx) throw new Error("useChats должен использоваться внутри ChatsProvider");
  return ctx;
}
