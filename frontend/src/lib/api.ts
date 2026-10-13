import type { DocumentRecord, QueryResponse } from "./types";

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // 응답이 JSON이 아닐 수도 있음 (예: 서버가 완전히 죽은 경우)
  }
  return `요청이 실패했습니다 (HTTP ${res.status})`;
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const res = await fetch(`${API_BASE_URL}/documents`);
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  return res.json();
}

export async function askQuestion(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(await extractErrorMessage(res));
  return res.json();
}
