import { useState } from "react";
import { exportFile, type CaseState, type ExportFormat } from "../api/generate";
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
  if (m.kind === "answer") return <AnswerView text={m.text} />;
  if (m.kind === "off_topic") {
    return (
      <div className="msg">
        <div className="offtopic">
          <div className="offtopic-title">Запрос не по теме</div>
          {m.text}
        </div>
      </div>
    );
  }
  return <IskView text={m.text} data={m.case} updated={m.updated} />;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      /* буфер обмена недоступен */
    }
  };

  return (
    <button className="chip" onClick={copy}>
      <CopyIcon />
      {copied ? "Скопировано" : "Копировать"}
    </button>
  );
}

function AnswerView({ text }: { text: string }) {
  return (
    <div className="msg">
      <div className="label">Ответ</div>
      <div className="answer">{text}</div>
      <div className="actions">
        <CopyButton text={text} />
      </div>
    </div>
  );
}

const EXPORTS: ExportFormat[] = ["docx", "pdf", "md"];

function IskView({ text, data, updated }: { text: string; data?: CaseState; updated?: boolean }) {
  const [busy, setBusy] = useState<ExportFormat | null>(null);

  const download = async (format: ExportFormat) => {
    if (!data) return;
    setBusy(format);
    try {
      downloadBlob(await exportFile(data.context, format), `iskovoe_zayavlenie.${format}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : `Не удалось получить .${format}`);
    } finally {
      setBusy(null);
    }
  };

  const sources = data?.sources.filter((s) => s.used) ?? [];

  return (
    <div className="msg">
      <div className="label">{updated ? "Исковое заявление (обновлено)" : "Исковое заявление"}</div>
      <div className="doc">{text}</div>
      <div className="actions">
        <CopyButton text={text} />
        <button
          className="chip"
          onClick={() => downloadBlob(new Blob([text], { type: "text/plain;charset=utf-8" }), "iskovoe_zayavlenie.txt")}
        >
          <DownloadIcon />Скачать .txt
        </button>
        {data &&
          EXPORTS.map((format) => (
            <button key={format} className="chip" onClick={() => download(format)} disabled={busy !== null}>
              <DownloadIcon />
              {busy === format ? `Готовлю .${format}…` : `Скачать .${format}`}
            </button>
          ))}
      </div>

      {data && data.missing.length > 0 && (
        <div className="hint-box">
          <div className="hint-title">Чтобы иск был полным, напишите в чат:</div>
          <ul>
            {data.missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="hint-note">Также можно задать любой вопрос по иску.</div>
        </div>
      )}

      {sources.length > 0 && (
        <details className="sources">
          <summary>Источники ({sources.length})</summary>
          {sources.map((s) => (
            <div className="source" key={s.tag}>
              <div className="source-head">
                [{s.tag}]{" "}
                {s.url ? (
                  <a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a>
                ) : (
                  s.title
                )}
              </div>
              <div className="source-text">{s.excerpt}</div>
            </div>
          ))}
        </details>
      )}
    </div>
  );
}
