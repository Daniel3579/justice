import { request, requestJSON } from "./client";

export interface EventStat {
  kind: string;
  total: number;
  week: number;
  today: number;
}

export interface AdminStats {
  users: number;
  users_week: number;
  admins: number;
  chats: number;
  events: EventStat[];
}

export interface IndexStatus {
  state: "idle" | "running" | "done" | "error";
  started_at: string | null;
  finished_at: string | null;
  chunks: number | null;
  error: string | null;
}

export interface DocumentInfo {
  name: string;
  size: number;
  modified: string;
}

export const adminApi = {
  stats: () => requestJSON<AdminStats>("/admin/stats"),
  documents: () => requestJSON<{ documents: DocumentInfo[]; index: IndexStatus }>("/admin/documents"),
  async upload(files: File[]) {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    return requestJSON<{ saved: string[] }>("/admin/documents", { method: "POST", body: form });
  },
  async remove(name: string) {
    await request(`/admin/documents/${encodeURIComponent(name)}`, { method: "DELETE" });
  },
  reindex: () => requestJSON<IndexStatus>("/admin/reindex", { method: "POST" }),
  reindexStatus: () => requestJSON<IndexStatus>("/admin/reindex"),
};
