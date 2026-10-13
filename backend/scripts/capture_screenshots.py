"""README용 스크린샷(업로드 화면, 채팅 화면)을 자동으로 찍어
docs/screenshots/에 저장한다.

백엔드를 LLM_PROVIDER=mock으로 띄우기 때문에 ANTHROPIC_API_KEY 없이도
실행할 수 있다. 백엔드/프론트엔드를 이 스크립트가 알아서 띄우고 끝나면 정리한다.

사용법 (최초 1회 설치):
    pip install -r requirements.txt -r requirements-dev.txt
    python -m playwright install chromium

실행:
    python scripts/capture_screenshots.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots"
SAMPLE_PDF = BACKEND_DIR / "sample_docs" / "remote_work_policy_sample.pdf"

BACKEND_PORT = 8098
FRONTEND_PORT = 4398
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"


def wait_for(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"{url}가 {timeout}초 안에 응답하지 않았습니다: {last_error}")


def main() -> None:
    if not SAMPLE_PDF.exists():
        sys.exit(f"샘플 PDF가 없습니다: {SAMPLE_PDF} (generate_sample_pdf.py를 먼저 실행하세요)")

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    data_dir = Path(tempfile.mkdtemp(prefix="doc_chatbot_screenshots_"))

    print("프론트엔드 빌드 중 (스크린샷용 백엔드 주소로 고정)...")
    subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        env={**os.environ, "VITE_API_BASE_URL": BACKEND_URL},
        check=True,
    )

    backend_env = {
        **os.environ,
        "DOC_CHATBOT_DATA_DIR": str(data_dir),
        "LLM_PROVIDER": "mock",
        "DOC_CHATBOT_ALLOWED_ORIGINS": FRONTEND_URL,
    }
    backend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(BACKEND_PORT),
        ],
        cwd=BACKEND_DIR,
        env=backend_env,
    )
    frontend_proc = subprocess.Popen(
        ["npm", "run", "preview", "--", "--port", str(FRONTEND_PORT), "--strictPort"],
        cwd=FRONTEND_DIR,
    )

    try:
        print("백엔드/프론트엔드 기동 대기 중...")
        wait_for(f"{BACKEND_URL}/health")
        wait_for(FRONTEND_URL)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 960, "height": 720})
            page.goto(FRONTEND_URL)

            print("업로드 화면 캡처 중...")
            page.get_by_role("button", name="문서 업로드").click()
            page.locator('input[type="file"]').set_input_files(str(SAMPLE_PDF))
            page.get_by_text(SAMPLE_PDF.name).wait_for(timeout=15000)
            page.screenshot(path=str(SCREENSHOT_DIR / "upload.png"))

            print("채팅 화면 캡처 중...")
            page.get_by_role("button", name="질문하기").click()
            page.get_by_placeholder("예: 원격근무는 며칠까지 가능한가요?").fill(
                "원격근무 신청은 언제까지 해야 하나요?"
            )
            page.get_by_role("button", name="보내기").click()
            page.locator(".chat-bubble.assistant").wait_for(timeout=15000)
            page.wait_for_timeout(300)  # 말풍선 렌더링 안정화
            page.screenshot(path=str(SCREENSHOT_DIR / "chat.png"))

            browser.close()

        print(f"완료: {SCREENSHOT_DIR}")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
        try:
            frontend_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            frontend_proc.kill()
        shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
