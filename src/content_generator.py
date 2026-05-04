"""
AI한입 — Claude API 콘텐츠 생성 모듈 v2
========================================
비기너 친화적 + 볼륨 업그레이드 버전
"""

import os
import json
import argparse
import anthropic
from pathlib import Path
from dotenv import dotenv_values

_env = dotenv_values(Path(__file__).parent.parent / "config" / ".env")
client = anthropic.Anthropic(api_key=_env.get("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────────────
# 공통 캐릭터 가이드 (모든 프롬프트에 적용)
# ─────────────────────────────────────────────────
CHARACTER = """
[AI한입 계정 캐릭터]
- AI 트렌드 매일 체크하고 직접 써본 고수
- 근데 설명은 "AI 처음 접하는 사람"도 이해하게
- 비기너가 읽었을 때 "아 이제 알겠다!" 느낌 주는 게 핵심
- 전문용어 쓸 땐 반드시 바로 옆에 쉬운 말로 설명
- 톤: 지식은 고수, 말투는 친구
- 절대 금지: 논문 말투, "~입니다체" 딱딱함, 영어 약어만 쓰기
"""

PROMPTS = {

    # ── 1. 오늘의 AI팁 (비기너 눈높이 강화) ──────────────────
    "daily_tip": CHARACTER + """
주제: {topic}

Threads 게시물 작성 규칙:
- 첫 줄: 비기너가 공감할 상황/고민으로 시작 (예: "ChatGPT 쓰는데 왜 나만 이상한 답이 나올까")
- 개념 설명: 중학생도 이해할 수 있게 (비유/예시 필수)
- 실습 가능: 오늘 바로 따라할 수 있는 방법 1가지 포함
- 마무리: 💾 저장해두면 언젠가 씁니다 (고정)
- 해시태그: #AI한입 #AI입문 #ChatGPT 중 2개

분량: 250~350자 (기존보다 50% 더 자세하게)
이모지: 3~4개
""",

    # ── 2. 비기너 완전정복 시리즈 (8개로 확장) ────────────────
    "thread": CHARACTER + """
주제: {topic}

AI를 처음 접하는 비기너를 위한 Threads 연속 게시물 8개 작성.
각 게시물 300자 이내.

구성:
1번: 훅 — 비기너가 겪는 진짜 고민/상황 공감
2번: "이게 뭔데?" — 개념을 3줄로 초간단 설명
3번: 왜 중요해? — 모르면 어떤 손해인지 현실적으로
4번: 쉬운 비유 — 일상 사물/상황에 빗대어 설명
5번: 비기너 실수 TOP1 — 가장 많이 하는 실수와 해결법
6번: 오늘 바로 해볼 것 — 따라하기 쉬운 실습 1단계
7번: 한 단계 업 — 좀 더 잘 쓰는 팁 1가지
8번: 요약 + CTA — 핵심 한 줄 + "팔로우하면 이런 거 매일 옵니다 🤖"

반드시 JSON으로만 반환:
{{"posts": ["1번", "2번", "3번", "4번", "5번", "6번", "7번", "8번"]}}
""",

    # ── 3. AI 뉴스 (비기너 번역 추가) ────────────────────────
    "news": CHARACTER + """
아래 AI 뉴스를 비기너도 이해하는 Threads 게시물로 변환.

뉴스 원문: {content}

형식:
🔥 AI 소식 — 비기너도 이해하는 버전

[한 줄 임팩트 요약]

쉽게 말하면:
→ [전문용어 없이 중학생도 알 수 있게 1-2줄]

뭐가 달라지냐면:
• [내 일상/업무에 미치는 영향 1]
• [내 일상/업무에 미치는 영향 2]
• [내 일상/업무에 미치는 영향 3]

지금 당장 해볼 것:
→ [비기너가 오늘 바로 할 수 있는 행동 1가지]

💬 한줄평: [솔직한 내 생각]
#AI뉴스 #AI한입 #AI입문
""",

    # ── 4. 퀴즈 (해설 강화) ──────────────────────────────────
    "quiz": CHARACTER + """
주제: {topic}

비기너가 재미있게 참여할 수 있는 퀴즈 게시물.
맞춰도 틀려도 배우는 게 있게.

형식:
🧠 AI 퀴즈 — 알면 고수, 몰라도 괜찮아요

[비기너 눈높이 질문] ← 생활 속 상황으로

① [보기 1]
② [보기 2]
③ [보기 3]
④ [보기 4]

💡 힌트: [너무 어렵지 않게 방향만 살짝]

댓글에 번호 달아주세요 👇
정답 + 자세한 설명은 내일 공개!

#AI퀴즈 #AI한입 #AI입문
""",

    # ── 5. 도구 리뷰 (비기너 시작법 추가) ───────────────────
    "tool_review": CHARACTER + """
도구: {topic}

AI 처음 쓰는 사람도 바로 시작할 수 있는 리뷰 작성.

형식:
🛠️ [도구명] 비기너 완전 가이드

한 줄 결론: [솔직하게]

비기너한테 좋은 점:
✅ [쉽게 시작할 수 있는 이유]
✅ [배우기 쉬운 이유]
✅ [실제 효과]

주의할 점:
⚠️ [비기너가 흔히 막히는 부분]

🚀 처음 시작하는 법 (3단계):
1. [아주 쉬운 첫 번째 단계]
2. [두 번째]
3. [세 번째]

이런 분께 딱:
→ [구체적인 상황 묘사]

#AI도구 #AI한입 #AI입문
""",

    # ── 6. NEW: 비기너 용어 해설 ─────────────────────────────
    "glossary": CHARACTER + """
AI 용어: {topic}

비기너가 처음 들었을 때 "이게 뭐지?" 하는 AI 용어를
완전히 이해하게 만드는 게시물.

형식:
📖 오늘의 AI 용어: [{topic}]

한 줄 정의: [전문용어 없이]

쉬운 비유:
→ [일상 생활 비유로 설명]

실제로 어디서 만나냐면:
• [상황 1]
• [상황 2]

알면 뭐가 좋아?
→ [실용적 이유]

비기너 행동 팁:
→ [오늘 바로 해볼 것]

💾 저장해두면 언젠가 씁니다
#AI용어 #AI한입 #AI입문
""",

    # ── 7. NEW: 비기너 실수 교정 ─────────────────────────────
    "mistake": CHARACTER + """
주제: {topic} 관련 비기너 실수

비기너들이 가장 많이 하는 실수를 콕 집어서 교정해주는 게시물.
"아 나 이랬는데!" 공감 유발이 핵심.

형식:
❌ AI 쓰면서 이 실수하고 있으면 손해

[공감되는 비기너 상황 묘사]

많은 분들이 이렇게 해요:
❌ [잘못된 방법 — 구체적으로]

근데 이렇게 하면 달라져요:
✅ [올바른 방법 — 따라할 수 있게]

왜 차이 나냐면:
→ [쉬운 이유 설명]

바로 고쳐보세요:
→ [지금 당장 할 수 있는 행동]

💾 저장해두면 언젠가 씁니다
#AI실수 #AI한입 #AI입문
"""
}

CONTENT_TYPES = list(PROMPTS.keys())


HUMANIZE_PROMPT = """
당신은 한국어 SNS 글의 AI 티를 제거하는 전문가입니다.
아래 Threads 게시물을 자연스러운 한국어로 다듬어주세요.

[핵심 규칙]
- 번역투 제거: "~에 대해서", "~를 통해", "~에 있어서" → 자연스럽게
- AI 관용구 제거: "결론적으로", "핵심적으로", "시사하는 바가 크다" → 삭제
- 결말 공식 제거: "~할 때다", "~해야 한다" → 평서문으로
- 단언하기: "~할 수 있다", "~로 보인다" → "~한다", "~다"
- 접속사 줄이기: "또한", "따라서", "나아가" 남발 금지
- 이모지·해시태그는 그대로 유지
- 의미·수치·고유명사는 절대 변경 금지
- 변경률 30% 초과 금지 (너무 많이 바꾸지 말 것)
- SNS 말투 유지 (격식체 → 격식체, 반말 → 반말)

[원문]
{text}

[지시]
자연스럽게 다듬은 결과만 출력하세요. 설명이나 메모 없이 본문만.
"""

def humanize(text: str) -> str:
    """AI 티 제거 — humanize-korean 룰 적용"""
    print(f"✨ humanize 처리 중...")
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2048,
        messages=[{"role": "user", "content": HUMANIZE_PROMPT.format(text=text)}]
    )
    result = msg.content[0].text.strip()
    print(f"✅ humanize 완료")
    return result


def generate_content(content_type: str, topic: str = "", content: str = "", humanize_output: bool = True) -> dict:
    """Claude API로 콘텐츠 초안 생성 + humanize 처리"""

    if content_type not in PROMPTS:
        raise ValueError(f"지원하지 않는 타입: {content_type}\n가능: {CONTENT_TYPES}")

    prompt = PROMPTS[content_type].format(topic=topic, content=content)

    print(f"🤖 Claude에게 [{content_type}] 초안 요청 중...")

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text

    if content_type == "thread":
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            parsed = json.loads(raw[start:end])
            posts = parsed["posts"]
            if humanize_output:
                posts = [humanize(p) for p in posts]
            # 마지막 게시물에만 홍보 + 해시태그 추가
            if posts:
                posts[-1] = add_promo_footer(posts[-1], content_type)
            return {"type": content_type, "posts": posts, "raw": raw}
        except Exception as e:
            print(f"⚠️ JSON 파싱 실패: {e}")
            return {"type": content_type, "posts": [raw], "raw": raw}

    text = humanize(raw) if humanize_output else raw
    text = add_promo_footer(text, content_type)
    return {"type": content_type, "text": text}


PROMO_FOOTER = """
📚 AI 같이 공부할 사람?
당근 모임 → daangn.com/kr/group/927162"""

# 해시태그 풀 — 벤치마킹 기반 (대형+중형+소형 조합)
HASHTAG_POOLS = {
    "daily_tip":   ["#ChatGPT", "#Claude", "#AI팁", "#AI공부", "#AI한입", "#프롬프트"],
    "thread":      ["#AI", "#ChatGPT", "#Claude", "#AI공부", "#AI한입", "#AI입문"],
    "news":        ["#AI뉴스", "#ChatGPT", "#Claude", "#AI", "#AI한입", "#테크뉴스"],
    "quiz":        ["#AI퀴즈", "#ChatGPT", "#AI공부", "#AI한입", "#AI입문"],
    "tool_review": ["#AI도구", "#ChatGPT", "#Claude", "#생산성", "#AI한입", "#AI추천"],
    "glossary":    ["#AI용어", "#ChatGPT", "#Claude", "#AI공부", "#AI한입", "#AI입문"],
    "mistake":     ["#ChatGPT", "#Claude", "#AI팁", "#AI공부", "#AI한입", "#AI주의"],
}


import re

def strip_markdown(text: str) -> str:
    """Threads는 마크다운을 렌더링하지 않으므로 모두 제거"""
    # **bold** / __bold__ → bold
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    # *italic* → italic (단, 별표 단독 줄은 보존 안 함)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", r"\1", text)
    # _italic_ → italic
    text = re.sub(r"(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)", r"\1", text)
    # `code` → code
    text = re.sub(r"`([^`]+?)`", r"\1", text)
    # ### heading / ## heading / # heading → heading
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # [text](url) → text (url)
    text = re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", r"\1 (\2)", text)
    # > blockquote → blockquote
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    # --- (수평선) → 빈 줄로
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    # 남은 ** 잔재 제거
    text = text.replace("**", "")
    # 연속 빈 줄 정리
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def add_promo_footer(text: str, content_type: str = "daily_tip") -> str:
    """
    게시물 하단에 당근 홍보 + 최적 해시태그 자동 삽입.
    마크다운 제거 + 텍스트 길이에 관계없이 항상 추가.
    """
    # 0. 마크다운 제거 (** ## ` 등)
    text = strip_markdown(text)

    # 1. 기존 해시태그 라인 제거 (Claude가 만든 것)
    lines = text.rstrip().split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        # 해시태그만 있는 라인은 제거
        if s and all(w.startswith("#") for w in s.split() if w):
            continue
        cleaned.append(line)

    body = "\n".join(cleaned).rstrip()

    # 2. 해시태그 6개 선택 (벤치마킹 기반)
    tags = " ".join(HASHTAG_POOLS.get(content_type, HASHTAG_POOLS["daily_tip"])[:6])

    # 3. 조합: 본문 + 홍보 + 해시태그
    return f"{body}\n{PROMO_FOOTER}\n\n{tags}"


def generate_weekly_batch(topics: dict) -> list:
    """
    1주일치 콘텐츠 한번에 생성
    topics = {"monday": ("daily_tip", "프롬프트 팁"), ...}
    """
    batch = []
    for day, (ctype, topic) in topics.items():
        print(f"\n📅 {day} 콘텐츠 생성 중...")
        result = generate_content(ctype, topic)
        result["day"] = day
        batch.append(result)
    return batch


def preview(result: dict):
    """생성된 콘텐츠 미리보기"""
    print("\n" + "="*50)
    print(f"📋 [{result['type']}] 미리보기")
    print("="*50)

    if result["type"] == "thread":
        for i, post in enumerate(result["posts"]):
            print(f"\n[{i+1}/{len(result['posts'])}]")
            print(post)
            print("-"*30)
    else:
        print(result.get("text", ""))

    print("="*50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI한입 콘텐츠 생성기 v2")
    parser.add_argument("--type", required=True, choices=CONTENT_TYPES)
    parser.add_argument("--topic", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    result = generate_content(args.type, args.topic, args.content)
    preview(result)

    if args.save:
        fname = f"../prompts/{args.type}_{args.topic[:20].replace(' ','_')}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 저장됨: {fname}")
