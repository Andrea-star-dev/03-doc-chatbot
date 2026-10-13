export interface DocumentRecord {
  doc_id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  uploaded_at: string;
}

export interface Source {
  doc_id: string;
  filename: string;
  page: number;
}

export interface QueryResponse {
  answer: string;
  used_context: boolean;
  sources: Source[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  isError?: boolean;
}
