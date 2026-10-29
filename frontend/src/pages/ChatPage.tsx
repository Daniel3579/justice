import { useEffect, useRef } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { sendChat, type CaseState, type ChatTurn } from "../api/generate";
import { Composer } from "../components/Composer";
import { MessageView } from "../components/MessageView";
import { useChats, type Message } from "../lib/ChatsContext";

function latestCase(messages: Message[]): CaseState | null {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role === "assistant" && m.case) return m.case;
  }
  return null;
}

function toHistory(messages: Message[]): ChatTurn[] {
  const turns: ChatTurn[] = [];
  for (const m of messages) {
    if (m.role === "user") turns.push({ role: "user", content: m.text });
    else if (m.role === "assistant")
      turns.push({ role: "assistant", content: m.kind === "answer" ? m.text : "[Составлено исковое заявление]" });
  }
  return turns;
}

export function ChatPage() {
  const { chatId } = useParams();
  const { getChat, createChat, updateChat } = useChats();
  const navigate = useNavigate();
  const chat = getChat(chatId);
  const stageRef = useRef<HTMLDivElement>(null);

  const busy = !!chat?.messages.some((m) => m.role === "pending");
  const hasCase = !!chat && latestCase(chat.messages) !== null;

  useEffect(() => {
    stageRef.current?.scrollTo({ top: stageRef.current.scrollHeight });
  }, [chat?.messages.length, chatId]);

  async function send(text: string) {
    const previous = chat?.messages ?? [];
    const id = chat?.id ?? createChat(text).id;
    if (!chat) navigate(`/c/${id}`);

    updateChat(id, (c) => ({ ...c, messages: [...c.messages, { role: "user", text }, { role: "pending" }] }));

    let reply: Message;
    try {
      const data = await sendChat(text, toHistory(previous), latestCase(previous));
      reply =
        data.type === "isk"
          ? { role: "assistant", kind: "isk", text: data.case.isk, case: data.case, updated: data.updated }
          : { role: "assistant", kind: "answer", text: data.answer };
    } catch (e) {
      reply = { role: "error", text: e instanceof Error ? e.message : "Не удалось получить ответ" };
    }
    updateChat(id, (c) => ({ ...c, messages: c.messages.map((m) => (m.role === "pending" ? reply : m)) }));
  }

  if (chatId && !chat) return <Navigate to="/" replace />;

  if (!chat) {
    return (
      <div className="stage">
        <div className="home">
          <h1>Чем могу помочь?</h1>
          <p>Опишите своими словами, как нарушили ваши права потребителя, а я подготовлю исковое заявление. Потом можно задать вопросы по нему.</p>
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
        <Composer
          key={chat.id}
          onSend={send}
          disabled={busy}
          placeholder={hasCase ? "Задайте вопрос или пришлите недостающие данные…" : undefined}
        />
      </div>
    </>
  );
}