import { useState } from "react";
import { askQuestion } from "../lib/api";
import type { ChatMessage } from "../lib/types";

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend() {
    const question = input.trim();
    if (!question || isLoading) return;

    const userMessage: ChatMessage = { id: newId(), role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          text: result.answer,
          sources: result.used_context ? result.sources : undefined,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          text: err instanceof Error ? err.message : "답변을 가져오지 못했습니다.",
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>문서에게 질문하기</h2>
      <p className="panel-description">
        업로드한 문서 내용을 근거로 답합니다. 근거가 없으면 모른다고 답합니다.
      </p>

      <div className="chat-log">
        {messages.length === 0 && (
          <p className="status-text">궁금한 내용을 물어보세요.</p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble ${msg.role} ${msg.isError ? "error" : ""}`}>
            <div className="chat-text">{msg.text}</div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="chat-sources">
                출처:{" "}
                {msg.sources
                  .map((s) => `${s.filename} ${s.page}페이지`)
                  .join(", ")}
              </div>
            )}
          </div>
        ))}
        {isLoading && <div className="chat-bubble assistant status-text">답변 생성 중...</div>}
      </div>

      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault();
          void handleSend();
        }}
      >
        <input
          type="text"
          value={input}
          placeholder="예: 원격근무는 며칠까지 가능한가요?"
          disabled={isLoading}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          보내기
        </button>
      </form>
    </div>
  );
}
