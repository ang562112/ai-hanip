"""
AI한입 — Threads 자동 게시 모듈
================================
사용법:
    python threads_publisher.py --test       # 연결 테스트
    python threads_publisher.py --post-text  # 텍스트 게시
"""

import os
import time
import json
import argparse
import requests
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(Path(__file__).parent.parent / "config" / ".env")

class ThreadsPublisher:
    def __init__(self):
        self.user_id = os.getenv("THREADS_USER_ID")
        self.access_token = os.getenv("THREADS_ACCESS_TOKEN")
        self.base_url = "https://graph.threads.net/v1.0"

        if not self.user_id or not self.access_token:
            raise ValueError("❌ THREADS_USER_ID, THREADS_ACCESS_TOKEN 환경변수를 설정하세요")

    def _create_container(self, params: dict) -> str:
        """미디어 컨테이너 생성 (1단계)"""
        params["access_token"] = self.access_token
        resp = requests.post(
            f"{self.base_url}/{self.user_id}/threads",
            params=params
        )
        resp.raise_for_status()
        data = resp.json()
        if "id" not in data:
            raise Exception(f"컨테이너 생성 실패: {data}")
        return data["id"]

    def _publish_container(self, creation_id: str) -> dict:
        """컨테이너 발행 (2단계)"""
        # Threads API는 컨테이너 생성 후 잠깐 대기 필요
        time.sleep(2)
        resp = requests.post(
            f"{self.base_url}/{self.user_id}/threads_publish",
            params={
                "creation_id": creation_id,
                "access_token": self.access_token
            }
        )
        resp.raise_for_status()
        return resp.json()

    def post_text(self, text: str) -> dict:
        """텍스트 게시물 발행"""
        print(f"📝 게시 중: {text[:50]}...")
        container_id = self._create_container({
            "media_type": "TEXT",
            "text": text
        })
        result = self._publish_container(container_id)
        print(f"✅ 게시 완료! ID: {result.get('id')}")
        return result

    def post_image(self, text: str, image_url: str) -> dict:
        """이미지 포함 게시물 발행"""
        print(f"🖼️ 이미지 게시 중...")
        container_id = self._create_container({
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text
        })
        result = self._publish_container(container_id)
        print(f"✅ 이미지 게시 완료! ID: {result.get('id')}")
        return result

    def post_thread_series(self, posts: list[str]) -> list[dict]:
        """
        딥다이브용 연속 Thread 게시
        첫 번째 게시물 이후는 reply로 자동 연결
        """
        print(f"🧵 Thread 시리즈 게시 중... (총 {len(posts)}개)")
        results = []
        reply_to_id = None

        for i, text in enumerate(posts):
            params = {
                "media_type": "TEXT",
                "text": text
            }
            if reply_to_id:
                params["reply_to_id"] = reply_to_id

            container_id = self._create_container(params)
            result = self._publish_container(container_id)
            reply_to_id = result["id"]
            results.append(result)
            print(f"  [{i+1}/{len(posts)}] 완료 ✅")
            time.sleep(1)  # 연속 게시 간 딜레이

        print(f"🎉 Thread 시리즈 완료!")
        return results

    def test_connection(self) -> bool:
        """API 연결 테스트"""
        print("🔍 Threads API 연결 테스트 중...")
        resp = requests.get(
            f"{self.base_url}/{self.user_id}",
            params={
                "fields": "id,username,threads_profile_picture_url",
                "access_token": self.access_token
            }
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 연결 성공!")
            print(f"   계정: @{data.get('username')}")
            print(f"   ID: {data.get('id')}")
            return True
        else:
            print(f"❌ 연결 실패: {resp.status_code}")
            print(resp.json())
            return False

    def get_insights(self) -> dict:
        """최근 게시물 인사이트 조회"""
        resp = requests.get(
            f"{self.base_url}/{self.user_id}/threads",
            params={
                "fields": "id,text,timestamp,like_count,reply_count,repost_count,views",
                "access_token": self.access_token,
                "limit": 10
            }
        )
        resp.raise_for_status()
        return resp.json()


# ──────────────────────────────────────────
# CLI 테스트용
# ──────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI한입 Threads Publisher")
    parser.add_argument("--test", action="store_true", help="연결 테스트")
    parser.add_argument("--post-text", type=str, help="텍스트 게시물 발행")
    parser.add_argument("--insights", action="store_true", help="인사이트 조회")
    args = parser.parse_args()

    publisher = ThreadsPublisher()

    if args.test:
        publisher.test_connection()
    elif args.post_text:
        publisher.post_text(args.post_text)
    elif args.insights:
        data = publisher.get_insights()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("옵션을 선택하세요: --test / --post-text '내용' / --insights")
