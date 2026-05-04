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
        ("tool_review",  "Claude가 ChatGPT보다 글 잘 쓰는 진짜 이유"),
        ("daily_tip",    "Claude한테 글 시킬 때 결과 2배 올리는 한 줄"),
        ("thread",       "Claude로 1시간 만에 보고서 끝내는 워크플로우"),
        ("quiz",         "Claude가 잘하는 것 vs ChatGPT가 잘하는 것"),
    ],
    1: [  # 화
        ("glossary",     "Claude의 Constitutional AI가 뭐길래 다른가"),
        ("mistake",      "Claude한테 영어로 시키는 게 무조건 좋다는 착각"),
        ("tool_review",  "Claude Projects 기능 — 한번 써보면 못 돌아감"),
        ("daily_tip",    "Claude한테 긴 문서 던질 때 잘 읽게 하는 법"),
    ],
    2: [  # 수
        ("thread",       "Claude로 코드 짜는 비기너용 5단계 가이드"),
        ("tool_review",  "Cursor + Claude — 개발자 생산성 끝판왕"),
        ("daily_tip",    "AI에게 단계별로 생각하게 하는 법"),
        ("glossary",     "컨텍스트 윈도우 — Claude가 200K로 큰 이유"),
    ],
    3: [  # 목
        ("glossary",     "MCP(Model Context Protocol) — Claude의 비밀 무기"),
        ("mistake",      "AI 답변 그대로 믿고 팩트체크 안 하는 실수"),
        ("news",         "이번 주 Claude/AI 핵심 업데이트 요약"),
        ("quiz",         "AI 모델 OX 퀴즈"),
    ],
    4: [  # 금
        ("tool_review",  "Claude Artifacts — 결과물이 바로 보이는 마법"),
        ("daily_tip",    "Claude로 주말 사이드프로젝트 기획하는 법"),
        ("thread",       "AI 잘 쓰는 사람들이 매일 하는 5가지 습관"),
        ("mistake",      "AI에게 인격 부여하면 망하는 이유"),
    ],
    5: [  # 토
        ("glossary",     "RAG — Claude가 외부 자료 읽는 원리"),
        ("daily_tip",    "Claude로 회의록 자동 정리하는 법"),
        ("tool_review",  "Claude vs GPT-5 — 솔직한 비교 후기"),
        ("quiz",         "프롬프트 잘 쓰는 사람 vs 못 쓰는 사람"),
    ],
    6: [  # 일
        ("daily_tip",    "한 주 마무리 — 이번 주 AI 활용 회고"),
        ("thread",       "다음 주 Claude로 더 잘하기 위한 준비"),
        ("glossary",     "에이전트(Agent) — AI의 다음 진화"),
        ("news",         "다음 주 주목할 Claude/AI 업데이트 미리보기"),
    ],
}

# 게시 시간 (인게이지먼트 높은 4슬롯)
# 09:00 출근길 / 12:00 점심 / 19:00 퇴근 후 / 22:00 잠자기 전
POST_TIMES = ["09:00", "12:00", "19:00", "22:00"]


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
    """백그라운드 자동 실행 (하루 4회 + 주말 자동 플랜 생성)"""
    print("🤖 AI한입 자동화 데몬 시작!")
    print(f"   게시 시간: {POST_TIMES}")
    print("   주간 플랜 자동 생성: 일요일 23:00")
    print("   Ctrl+C로 종료\n")

    for i, t in enumerate(POST_TIMES):
        schedule.every().day.at(t).do(lambda i=i: run_slot(i))

    # 일요일 23:00 다음 주 플랜 자동 생성
    schedule.every().sunday.at("23:00").do(run_weekly_planner)

    while True:
        schedule.run_pending()
        time.sleep(60)


def run_weekly_planner():
    """주간 플랜 자동 생성 + scheduler.py 갱신"""
    print(f"\n📋 다음 주 플랜 자동 생성 시작...")
    try:
        from weekly_planner import generate_next_week, save_plan
        plan = generate_next_week()
        save_plan(plan)
        print("✅ 다음 주 플랜 갱신 완료")
    except Exception as e:
        print(f"❌ 플랜 생성 실패: {e}")


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
