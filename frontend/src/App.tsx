import { useState } from "react";
import "./App.css";
import { ChatPanel } from "./components/ChatPanel";
import { UploadPanel } from "./components/UploadPanel";

type Tab = "upload" | "chat";

function App() {
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <div className="app">
      <header className="app-header">
        <h1>사내 문서 검색 챗봇</h1>
        <nav className="tabs">
          <button
            className={tab === "upload" ? "active" : ""}
            onClick={() => setTab("upload")}
          >
            문서 업로드
          </button>
          <button
            className={tab === "chat" ? "active" : ""}
            onClick={() => setTab("chat")}
          >
            질문하기
          </button>
        </nav>
      </header>

      <main>{tab === "upload" ? <UploadPanel /> : <ChatPanel />}</main>
    </div>
  );
}

export default App;
