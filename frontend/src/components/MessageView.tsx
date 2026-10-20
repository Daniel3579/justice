import { useState } from "react";
import { generateDocx } from "../api/generate";
import type { Message } from "../lib/ChatsContext";
import { downloadBlob } from "../lib/format";
import { CopyIcon, DownloadIcon } from "./Icons";

export function MessageView({ m }: { m: Message }) {
  if (m.role === "user") {
    return (
      <div className="msg user">
        <div className="bubble">{m.text}</div>
      </div>
    );
  }
  if (m.role === "pending") {
    return (
      <div className="msg">
        <div className="label">
          <span className="typing"><i /><i /><i /></span>
          Анализирую ситуацию и подбираю нормы права…
        </div>
      </div>
    );
  }
  if (m.role === "error") {
    return (
      <div className="msg">
        <div className="error-box">{m.text}</div>
      </div>
    );
  }
  return <IskView text={m.text} source={m.source} />;
}

function IskView({ text, source }: { text: string; source: string }) {
  const [copied, setCopied] = useState(false);
  const [docxBusy, setDocxBusy] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* буфер обмена недоступен */
    }
  };

  const docx = async () => {
    setDocxBusy(true);
    try {
      downloadBlob(await generateDocx(source), "iskovoe_zayavlenie.docx");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось получить .docx");
    } finally {
      setDocxBusy(false);
    }
  };

  return (
    <div className="msg">
      <div className="label">Исковое заявление</div>
      <div className="doc">{text}</div>
      <div className="actions">
        <button className="chip" onClick={copy}><CopyIcon />{copied ? "Скопировано" : "Копировать"}</button>
        <button className="chip" onClick={() => downloadBlob(new Blob([text], { type: "text/plain;charset=utf-8" }), "iskovoe_zayavlenie.txt")}>
          <DownloadIcon />Скачать .txt
        </button>
        <button className="chip" onClick={docx} disabled={docxBusy}>
          <DownloadIcon />{docxBusy ? "Готовлю .docx…" : "Скачать .docx"}
        </button>
      </div>
    </div>
  );
}
