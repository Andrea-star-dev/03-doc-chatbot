"""테스트/데모용 샘플 PDF 생성기. 실제 회사 문서 아님, 직접 작성한 가짜 사내 규정 텍스트."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

KOREAN_FONT = "HYSMyeongJo-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(KOREAN_FONT))

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "sample_docs"

PAGES = [
    [
        "사내 원격근무 규정 (샘플 문서)",
        "",
        "1. 목적",
        "이 규정은 임직원의 원격근무 신청, 승인, 근태 관리 기준을 정한다.",
        "",
        "2. 적용 대상",
        "입사 후 3개월이 지난 정규직 임직원은 주 3일까지 원격근무를 신청할 수 있다.",
        "수습 기간 중인 임직원은 팀장 승인을 받은 경우에만 예외적으로 허용된다.",
    ],
    [
        "3. 신청 절차",
        "원격근무를 원하는 임직원은 희망일 2일 전까지 인사 시스템에 신청해야 한다.",
        "팀장은 신청 후 1일 이내에 승인 또는 반려해야 하며, 반려 시 이유를 명시해야 한다.",
        "",
        "4. 근태 확인",
        "원격근무일에는 오전 10시까지 업무 시작을 팀 채널에 공유해야 한다.",
        "오후 6시 이후에는 업무 종료를 공유하고, 특별한 사유 없이 연락이 되지 않으면",
        "결근으로 처리될 수 있다.",
    ],
    [
        "5. 장비 및 보안",
        "회사 지급 노트북 외의 장비로는 사내 시스템에 접속할 수 없다.",
        "공용 와이파이 사용 시 반드시 VPN을 통해 접속해야 한다.",
        "",
        "6. 기타",
        "이 규정에 명시되지 않은 사항은 일반 근태 규정을 따른다.",
    ],
]


def generate(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    for page_lines in PAGES:
        c.setFont(KOREAN_FONT, 12)
        y = height - 60
        for line in page_lines:
            c.drawString(50, y, line)
            y -= 22
        c.showPage()

    c.save()
    return output_path


def generate_blank(output_path: Path) -> Path:
    """텍스트가 전혀 없는 PDF (스캔 이미지 PDF 등을 흉내낸 테스트용)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.showPage()
    c.save()
    return output_path


def main() -> None:
    path = generate(OUTPUT_DIR / "remote_work_policy_sample.pdf")
    print(f"샘플 PDF 생성 완료: {path}")


if __name__ == "__main__":
    main()
