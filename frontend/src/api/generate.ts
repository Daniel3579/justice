import { request, requestJSON } from "./client";

export interface GenerateResponse {
  facts: unknown;
  isk: string;
  sources: { local: string; web: string };
}

/** POST /generate — текст иска (JSON). */
export function generateIsk(text: string, signal?: AbortSignal) {
  return requestJSON<GenerateResponse>("/generate", {
    method: "POST",
    body: JSON.stringify({ text }),
    signal,
  });
}

/** POST /generate/docx — готовый .docx. Сейчас бэкенд генерирует иск заново по исходному тексту. */
export async function generateDocx(text: string): Promise<Blob> {
  const r = await request("/generate/docx", { method: "POST", body: JSON.stringify({ text }) });
  return r.blob();
}
