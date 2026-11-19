import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";
import { adminApi, type AdminStats, type DocumentInfo, type IndexStatus } from "../api/admin";

const EVENT_LABELS: Record<string, string> = {
  isk: "Составлено исков",
  isk_update: "Обновлено исков",
  answer: "Ответов на вопросы",
  off_topic: "Запросов не по теме",
  error: "Ошибок генерации",
};

const INDEX_LABELS: Record<IndexStatus["state"], string> = {
  idle: "Не запускалась с момента старта сервера",
  running: "Выполняется…",
  done: "Завершена",
  error: "Ошибка",
};

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} МБ`;
}

function formatDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString("ru-RU") : "—";
}

export function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [index, setIndex] = useState<IndexStatus | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const fail = (e: unknown) => setMessage({ ok: false, text: e instanceof Error ? e.message : "Ошибка запроса" });

  const loadDocuments = useCallback(async () => {
    const data = await adminApi.documents();
    setDocuments(data.documents);
    setIndex(data.index);
  }, []);

  useEffect(() => {
    adminApi.stats().then(setStats).catch(fail);
    loadDocuments().catch(fail);
  }, [loadDocuments]);

  useEffect(() => {
    if (index?.state !== "running") return;
    const timer = setInterval(() => {
      adminApi
        .reindexStatus()
        .then((s) => {
          setIndex(s);
          if (s.state === "done") setMessage({ ok: true, text: `Переиндексация завершена: ${s.chunks} фрагментов` });
          if (s.state === "error") setMessage({ ok: false, text: `Переиндексация не удалась: ${s.error}` });
        })
        .catch(fail);
    }, 3000);
    return () => clearInterval(timer);
  }, [index?.state]);

  const upload = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (!files.length) return;
    setBusy(true);
    setMessage(null);
    try {
      const { saved } = await adminApi.upload(files);
      await loadDocuments();
      setMessage({ ok: true, text: `Загружено: ${saved.join(", ")}. Запустите переиндексацию, чтобы документы попали в поиск.` });
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (name: string) => {
    if (!confirm(`Удалить «${name}»? После удаления запустите переиндексацию.`)) return;
    setBusy(true);
    setMessage(null);
    try {
      await adminApi.remove(name);
      await loadDocuments();
      setMessage({ ok: true, text: `Удалён: ${name}. Запустите переиндексацию.` });
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  };

  const reindex = async () => {
    setMessage(null);
    try {
      setIndex(await adminApi.reindex());
    } catch (err) {
      fail(err);
    }
  };

  const running = index?.state === "running";

  return (
    <div className="stage">
      <div className="page admin">
        <h2>Администрирование</h2>

        {message && <p className={`note ${message.ok ? "ok" : "err"} admin-message`}>{message.text}</p>}

        <div className="card-title">Статистика</div>
        <div className="card">
          {stats ? (
            <>
              <div className="stat-grid">
                <div className="stat">
                  <div className="stat-value">{stats.users}</div>
                  <div className="stat-label">пользователей</div>
                  <div className="stat-sub">+{stats.users_week} за 7 дней</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.chats}</div>
                  <div className="stat-label">чатов</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.admins}</div>
                  <div className="stat-label">администраторов</div>
                </div>
              </div>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Событие</th>
                    <th>Сегодня</th>
                    <th>7 дней</th>
                    <th>Всего</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.events.length === 0 && (
                    <tr>
                      <td colSpan={4} className="v">Событий пока нет</td>
                    </tr>
                  )}
                  {stats.events.map((e) => (
                    <tr key={e.kind}>
                      <td>{EVENT_LABELS[e.kind] ?? e.kind}</td>
                      <td>{e.today}</td>
                      <td>{e.week}</td>
                      <td>{e.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <div className="row v">Загрузка…</div>
          )}
        </div>

        <div className="card-title">База документов</div>
        <div className="card">
          <div className="row">
            <div>
              <div className="k">Поисковый индекс</div>
              <div className="v">
                {index ? INDEX_LABELS[index.state] : "—"}
                {index?.state === "done" && ` · ${index.chunks} фрагментов · ${formatDate(index.finished_at)}`}
              </div>
            </div>
            <button className="btn primary" onClick={reindex} disabled={running || busy}>
              {running ? "Индексация…" : "Переиндексировать"}
            </button>
          </div>
          <div className="row">
            <div>
              <div className="k">Добавить документы</div>
              <div className="v">PDF с текстовым слоем, до 50 МБ</div>
            </div>
            <button className="btn" onClick={() => fileInput.current?.click()} disabled={busy || running}>
              Загрузить PDF
            </button>
            <input ref={fileInput} type="file" accept="application/pdf,.pdf" multiple hidden onChange={upload} />
          </div>
          {documents.length === 0 && <div className="row v">Документов нет</div>}
          {documents.map((d) => (
            <div className="row" key={d.name}>
              <div className="doc-info">
                <div className="doc-name">{d.name}</div>
                <div className="v">
                  {formatSize(d.size)} · {formatDate(d.modified)}
                </div>
              </div>
              <button className="btn danger" onClick={() => remove(d.name)} disabled={busy || running}>
                Удалить
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
