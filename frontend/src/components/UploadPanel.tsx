import { useEffect, useRef, useState } from "react";
import { listDocuments, uploadDocument } from "../lib/api";
import type { DocumentRecord } from "../lib/types";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ko-KR");
  } catch {
    return iso;
  }
}

export function UploadPanel() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function refreshList() {
    setIsLoadingList(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "문서 목록을 불러오지 못했습니다.");
    } finally {
      setIsLoadingList(false);
    }
  }

  useEffect(() => {
    void refreshList();
  }, []);

  async function handleFileSelected(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("PDF 파일만 업로드할 수 있습니다.");
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "업로드에 실패했습니다.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="panel">
      <h2>문서 업로드</h2>
      <p className="panel-description">
        PDF 파일을 올리면 내용을 분석해 채팅에서 질문할 수 있게 됩니다.
      </p>

      <div className="upload-box">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          disabled={isUploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFileSelected(file);
          }}
        />
        {isUploading && <span className="status-text">업로드 중...</span>}
      </div>

      {error && <div className="error-box">{error}</div>}

      <h3>업로드된 문서</h3>
      {isLoadingList ? (
        <p className="status-text">불러오는 중...</p>
      ) : documents.length === 0 ? (
        <p className="status-text">아직 업로드된 문서가 없습니다.</p>
      ) : (
        <table className="doc-table">
          <thead>
            <tr>
              <th>파일명</th>
              <th>페이지</th>
              <th>청크</th>
              <th>업로드 시각</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.doc_id}>
                <td>{doc.filename}</td>
                <td>{doc.num_pages}</td>
                <td>{doc.num_chunks}</td>
                <td>{formatDate(doc.uploaded_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
