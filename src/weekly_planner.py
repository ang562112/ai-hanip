"""
AI한입 — 주간 플랜 자동 생성기
=================================
매주 일요일 23:00에 다음 주 콘텐츠 플랜 자동 생성
"""

import sys
import os
import json
from pathlib import Path
from content_generator import client

PLAN_FILE = Path(__file__).parent.parent / "prompts" / "weekly_plans.json"

PLANNER_PROMPT = """
AI한입 Threads 계정 다음 주 콘텐츠 플랜을 짜줘.

조건:
- 타겟: AI 비기너 (직장인/대학생)
- 하루 4개씩 (인게이지먼트 높은 시간대 4슬롯)
- 슬롯별 추천 타입:
  * 슬롯 0 (오전 9시): daily_tip 또는 glossary (출근길 가벼운 학습)
  * 슬롯 1 (점심 12시): tool_review 또는 mistake (점심시간 빠른 확인)
  * 슬롯 2 (저녁 7시): thread 또는 news (퇴근 후 깊이있는 콘텐츠)
  * 슬롯 3 (밤 10시): quiz 또는 daily_tip (잠자기 전 가벼운 참여)
- 타입 7종: daily_tip / thread / news / quiz / tool_review / glossary / mistake
- 다양성 중요: 같은 타입 연속 X, 주제 겹침 X

이미 사용한 주제 (피해야 함):
{used_topics}

응답은 반드시 JSON으로만:
{{
  "0": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "1": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "2": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "3": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "4": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "5": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]],
  "6": [["타입", "주제"], ["타입", "주제"], ["타입", "주제"], ["타입", "주제"]]
}}

키 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일
"""


def load_used_topics() -> list:
    """과거 사용한 주제 모두 가져오기"""
    if not PLAN_FILE.exists():
        return []
    with open(PLAN_FILE, encoding='utf-8') as f:
        data = json.load(f)
    used = []
    for week in data.get("weeks", []):
        for day_posts in week["plan"].values():
            for ctype, topic in day_posts:
                used.append(topic)
    return used


def generate_next_week() -> dict:
    """다음 주 플랜 생성"""
    used = load_used_topics()
    print(f"📚 과거 사용 주제 {len(used)}개 회피")

    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": PLANNER_PROMPT.format(used_topics="\n".join(f"- {t}" for t in used[-50:]))
        }]
    )
    raw = msg.content[0].text
    start = raw.find("{")
    end = raw.rfind("}") + 1
    plan = json.loads(raw[start:end])
    # 키를 int로 변환
    plan = {int(k): v for k, v in plan.items()}
    return plan


def save_plan(plan: dict):
    """생성된 플랜 저장 + scheduler.py에 자동 반영"""
    from datetime import datetime, timedelta

    # 이번 주 플랜 백업
    data = {"weeks": []}
    if PLAN_FILE.exists():
        with open(PLAN_FILE, encoding='utf-8') as f:
            data = json.load(f)

    week_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    data["weeks"].append({
        "week_start": week_start,
        "generated_at": datetime.now().isoformat(),
        "plan": {str(k): v for k, v in plan.items()}
    })

    PLAN_FILE.parent.mkdir(exist_ok=True)
    with open(PLAN_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # scheduler.py 업데이트
    update_scheduler(plan)
    print(f"✅ 플랜 저장 완료 (week starting {week_start})")


def update_scheduler(plan: dict):
    """scheduler.py의 WEEKLY_PLAN 자동 갱신"""
    sched_file = Path(__file__).parent / "scheduler.py"
    with open(sched_file, encoding='utf-8') as f:
        content = f.read()

    # WEEKLY_PLAN 블록 생성
    days = ["월", "화", "수", "목", "금", "토", "일"]
    new_block = "WEEKLY_PLAN = {\n"
    for d in range(7):
        new_block += f"    {d}: [  # {days[d]}\n"
        for ctype, topic in plan[d]:
            t_safe = topic.replace('"', "'")
            new_block += f'        ("{ctype}", "{t_safe}"),\n'
        new_block += f"    ],\n"
    new_block += "}"

    # 기존 WEEKLY_PLAN 교체
    import re
    content = re.sub(r"WEEKLY_PLAN = \{[\s\S]+?\n\}", new_block, content, count=1)

    with open(sched_file, "w", encoding='utf-8') as f:
        f.write(content)
    print("✅ scheduler.py 자동 갱신 완료")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("🤖 다음 주 콘텐츠 플랜 자동 생성 중...")
    plan = generate_next_week()
    save_plan(plan)
    print("\n📅 생성된 플랜:")
    days = ["월","화","수","목","금","토","일"]
    for d in range(7):
        print(f"\n{days[d]}요일:")
        for slot, (ctype, topic) in enumerate(plan[d]):
            times = ["09:00", "12:00", "19:00", "22:00"]
            print(f"  [{times[slot]}] {ctype}: {topic}")
