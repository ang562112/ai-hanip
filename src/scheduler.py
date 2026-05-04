"""
AI한입 — 자동화 스케줄러
==========================
매일 자동으로 콘텐츠 생성 → Threads 게시
python scheduler.py --run     # 오늘 콘텐츠 즉시 실행
python scheduler.py --week    # 이번 주 미리보기
python scheduler.py --daemon  # 백그라운드 스케줄 실행
"""

import sys
import time
import json
import argparse
import schedule
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

src = Path(__file__).parent
sys.path.insert(0, str(src))

from content_generator import generate_content, preview
from threads_direct import ThreadsDirect

pub = ThreadsDirect()

# ─────────────────────────────────────────────────
# 주간 콘텐츠 플랜
# 타입: daily_tip / thread / news / quiz /
#       tool_review / glossary / mistake
# ─────────────────────────────────────────────────
WEEKLY_PLAN = {
    0: [  # 월
        ("daily_tip",    "AI에게 단계별로 생각하게 하는 법 (Let's think step by step)"),
        ("glossary",     "LLM(대규모 언어 모델)이 뭔가요"),
    ],
    1: [  # 화
        ("tool_review",  "Notion AI 실제 써보니 — 장단점 솔직 후기"),
        ("mistake",      "AI 답변 그대로 믿고 팩트체크 안 하는 실수"),
    ],
    2: [  # 수
        ("thread",       "AI로 이메일 작성 시간 10분에서 2분 만든 방법"),
        ("quiz",         "이 문장 AI가 쓴 걸까 사람이 쓴 걸까"),
    ],
    3: [  # 목
        ("daily_tip",    "AI한테 더 자세히 보다 효과적인 말"),
        ("glossary",     "파인튜닝 vs 프롬프트 엔지니어링 차이"),
    ],
    4: [  # 금
        ("tool_review",  "Gamma AI로 발표자료 5분 만들기"),
        ("thread",       "대학생이 AI로 레포트 윤리적으로 활용하는 법"),
    ],
    5: [  # 토
        ("mistake",      "AI한테 한 번에 너무 많이 요청하는 실수"),
        ("daily_tip",    "AI로 영어 공부 효율 2배 올리는 법"),
    ],
    6: [  # 일
        ("quiz",         "AI 용어 OX 퀴즈"),
        ("glossary",     "에이전트(Agent) — AI의 다음 진화"),
    ],
}

# 게시 시간
POST_TIMES = ["08:00", "19:00"]  # 오전 8시, 저녁 7시


def run_today():
    """오늘 요일에 맞는 콘텐츠 생성 + 게시"""
    weekday = datetime.now().weekday()
    plan = WEEKLY_PLAN.get(weekday, [])
    day_names = ["월","화","수","목","금","토","일"]

    print(f"\n{'='*50}")
    print(f"📅 오늘({day_names[weekday]}요일) 콘텐츠 실행")
    print(f"{'='*50}")

    for i, (ctype, topic) in enumerate(plan):
        print(f"\n[{i+1}/{len(plan)}] {ctype} — {topic}")
        result = generate_content(ctype, topic)
        preview(result)

        # 게시
        if result["type"] == "thread":
            pub.post_thread_series(result["posts"])
        else:
            pub.post_text(result["text"])

        # 게시 간 딜레이 (스팸 방지)
        if i < len(plan) - 1:
            print("⏳ 다음 게시까지 30초 대기...")
            time.sleep(30)

    print(f"\n✅ 오늘 콘텐츠 완료!")
    log_result(plan, weekday)


def preview_week():
    """이번 주 전체 플랜 미리보기"""
    day_names = ["월","화","수","목","금","토","일"]
    print("\n📅 이번 주 AI한입 콘텐츠 플랜")
    print("="*50)
    for day_num, posts in WEEKLY_PLAN.items():
        print(f"\n{day_names[day_num]}요일:")
        for ctype, topic in posts:
            print(f"  [{ctype}] {topic}")
    print("="*50)


def log_result(plan: list, weekday: int):
    """게시 결과 로그 저장"""
    log_path = Path(__file__).parent.parent / "prompts" / "post_log.json"
    logs = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)

    logs.append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "weekday": weekday,
        "posts": [{"type": t, "topic": tp} for t, tp in plan]
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def run_daemon():
    """백그라운드 자동 실행 (매일 오전 8시, 저녁 7시)"""
    print("🤖 AI한입 자동화 데몬 시작!")
    print(f"   게시 시간: {POST_TIMES}")
    print("   Ctrl+C로 종료\n")

    # 오전 8시 — 첫 번째 콘텐츠
    schedule.every().day.at(POST_TIMES[0]).do(lambda: run_slot(0))
    # 저녁 7시 — 두 번째 콘텐츠
    schedule.every().day.at(POST_TIMES[1]).do(lambda: run_slot(1))

    while True:
        schedule.run_pending()
        time.sleep(60)


def run_slot(slot_index: int):
    """특정 슬롯(0=오전, 1=저녁) 콘텐츠만 실행"""
    weekday = datetime.now().weekday()
    plan = WEEKLY_PLAN.get(weekday, [])

    if slot_index >= len(plan):
        print(f"⚠️ 슬롯 {slot_index} 콘텐츠 없음")
        return

    ctype, topic = plan[slot_index]
    print(f"\n⏰ {POST_TIMES[slot_index]} 자동 게시: [{ctype}] {topic}")

    result = generate_content(ctype, topic)

    if result["type"] == "thread":
        pub.post_thread_series(result["posts"])
    else:
        pub.post_text(result["text"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI한입 스케줄러")
    parser.add_argument("--run",    action="store_true", help="오늘 콘텐츠 즉시 실행")
    parser.add_argument("--week",   action="store_true", help="이번 주 플랜 보기")
    parser.add_argument("--daemon", action="store_true", help="백그라운드 자동 실행")
    parser.add_argument("--slot",   type=int, default=0, help="특정 슬롯만 실행 (0 또는 1)")
    args = parser.parse_args()

    if args.run:
        run_today()
    elif args.week:
        preview_week()
    elif args.daemon:
        run_daemon()
    else:
        preview_week()
        print("\n사용법: --run (즉시실행) / --week (플랜보기) / --daemon (자동화)")
