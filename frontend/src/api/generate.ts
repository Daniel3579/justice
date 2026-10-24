import { request, requestJSON } from "./client";

export interface Source {
  tag: string;
  title: string;
  url: string | null;
  excerpt: string;
  used: boolean;
}

export interface CaseState {
  story: string;
  facts: Record<string, unknown>;
  context: Record<string, unknown>;
  isk: string;
  missing: string[];
  sources: Source[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export type ChatResponse =
  | { type: "isk"; updated: boolean; case: CaseState }
  | { type: "answer"; answer: string };

export function sendChat(message: string, history: ChatTurn[], current: CaseState | null, signal?: AbortSignal) {
  return requestJSON<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, history, case: current }),
    signal,
  });
}

export async function exportDocx(context: CaseState["context"]): Promise<Blob> {
  const r = await request("/export/docx", { method: "POST", body: JSON.stringify({ context }) });
  return r.blob();
}