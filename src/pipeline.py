"""
AI한입 — 메인 파이프라인
==========================
생성 → 미리보기 → 승인 → 게시 전체 플로우

사용법:
    python pipeline.py                          # 대화형 모드
    python pipeline.py --auto --type daily_tip  # 자동 모드 (n8n 연동용)
"""

import os
import json
import argparse
from datetime import datetime
from content_generator import generate_content, preview
from threads_publisher import ThreadsPublisher

QUEUE_FILE = "../prompts/queue.json"


def load_queue() -> list:
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_queue(queue: list):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def add_to_queue(result: dict, topic: str):
    queue = load_queue()
    queue.append({
        "id": len(queue) + 1,
        "created_at": datetime.now().isoformat(),
        "topic": topic,
        "status": "pending",  # pending / approved / posted / rejected
        "content": result
    })
    save_queue(queue)
    print(f"📥 큐에 추가됨 (ID: {queue[-1]['id']})")
    return queue[-1]["id"]


def interactive_mode():
    """대화형 모드: 생성 → 확인 → 바로 게시"""

    print("\n🤖 AI한입 콘텐츠 파이프라인")
    print("="*40)

    # 타입 선택
    types = ["daily_tip", "thread", "news", "quiz", "tool_review"]
    print("\n콘텐츠 타입 선택:")
    for i, t in enumerate(types, 1):
        print(f"  {i}. {t}")
    choice = int(input("\n번호 입력: ")) - 1
    content_type = types[choice]

    # 주제 입력
    if content_type == "news":
        topic = ""
        content = input("뉴스 원문 붙여넣기: ")
    else:
        topic = input("주제 입력: ")
        content = ""

    # 콘텐츠 생성
    result = generate_content(content_type, topic, content)
    preview(result)

    # 승인
    action = input("\n어떻게 할까요? [p]게시 / [q]큐저장 / [r]재생성 / [x]취소: ").lower()

    if action == "p":
        publish_content(result)
    elif action == "q":
        add_to_queue(result, topic)
    elif action == "r":
        print("재생성 중...")
        result = generate_content(content_type, topic, content)
        preview(result)
        if input("게시할까요? [y/n]: ").lower() == "y":
            publish_content(result)
    else:
        print("취소됨")


def publish_content(result: dict):
    """실제 Threads 게시"""
    publisher = ThreadsPublisher()

    if result["type"] == "thread":
        publisher.post_thread_series(result["posts"])
    else:
        publisher.post_text(result["text"])


def auto_mode(content_type: str, topic: str, auto_post: bool = False):
    """
    자동 모드 (n8n 웹훅에서 호출)
    결과를 JSON으로 출력
    """
    result = generate_content(content_type, topic)

    if auto_post:
        publish_content(result)
        output = {"status": "posted", "content": result}
    else:
        item_id = add_to_queue(result, topic)
        output = {"status": "queued", "id": item_id, "content": result}

    print(json.dumps(output, ensure_ascii=False))
    return output


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI한입 파이프라인")
    parser.add_argument("--auto", action="store_true", help="자동 모드 (n8n용)")
    parser.add_argument("--type", help="콘텐츠 타입")
    parser.add_argument("--topic", default="", help="주제")
    parser.add_argument("--post", action="store_true", help="바로 게시 (승인 스킵)")
    args = parser.parse_args()

    if args.auto and args.type:
        auto_mode(args.type, args.topic, args.post)
    else:
        interactive_mode()
