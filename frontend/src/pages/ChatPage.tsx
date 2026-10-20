import { useEffect, useRef } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { generateIsk } from "../api/generate";
import { Composer } from "../components/Composer";
import { MessageView } from "../components/MessageView";
import { useChats, type Message } from "../lib/ChatsContext";

export function ChatPage() {
  const { chatId } = useParams();
  const { getChat, createChat, updateChat } = useChats();
  const navigate = useNavigate();
  const chat = getChat(chatId);
  const stageRef = useRef<HTMLDivElement>(null);

  const busy = !!chat?.messages.some((m) => m.role === "pending");

  useEffect(() => {
    stageRef.current?.scrollTo({ top: stageRef.current.scrollHeight });
  }, [chat?.messages.length, chatId]);

  async function send(text: string) {
    const id = chat?.id ?? createChat(text).id;
    if (!chat) navigate(`/c/${id}`);

    updateChat(id, (c) => ({ ...c, messages: [...c.messages, { role: "user", text }, { role: "pending" }] }));

    let reply: Message;
    try {
      const data = await generateIsk(text);
      reply = { role: "assistant", text: data.isk, source: text };
    } catch (e) {
      reply = { role: "error", text: e instanceof Error ? e.message : "Не удалось получить ответ" };
    }
    updateChat(id, (c) => ({ ...c, messages: c.messages.map((m) => (m.role === "pending" ? reply : m)) }));
  }

  // ссылка на удалённый или чужой чат
  if (chatId && !chat) return <Navigate to="/" replace />;

  if (!chat) {
    return (
      <div className="stage">
        <div className="home">
          <h1>Чем могу помочь?</h1>
          <p>Опишите своими словами, как нарушили ваши права потребителя, а я подготовлю исковое заявление.</p>
          <Composer onSend={send} />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="stage" ref={stageRef}>
        <div className="thread">
          {chat.messages.map((m, i) => (
            <MessageView key={i} m={m} />
          ))}
        </div>
      </div>
      <div className="bottom">
        <Composer key={chat.id} onSend={send} disabled={busy} />
      </div>
    </>
  );
}
