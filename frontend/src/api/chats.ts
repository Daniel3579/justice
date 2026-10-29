import { request, requestJSON } from "./client";
import type { Chat } from "../lib/ChatsContext";

export function fetchChats() {
  return requestJSON<Chat[]>("/chats");
}

export async function saveChat(chat: Chat) {
  await request(`/chats/${encodeURIComponent(chat.id)}`, {
    method: "PUT",
    body: JSON.stringify({
      title: chat.title,
      messages: chat.messages.filter((m) => m.role !== "pending"),
    }),
  });
}

export async function removeChat(id: string) {
  await request(`/chats/${encodeURIComponent(id)}`, { method: "DELETE" });
}