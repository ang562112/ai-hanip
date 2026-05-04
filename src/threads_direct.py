"""
Threads API 직접 게시 모듈 (Meta Developer 토큰 사용)
=====================================================
Ayrshare 우회 — 영구 무료
"""

import os
import time
import requests
from pathlib import Path
from dotenv import dotenv_values

_env = dotenv_values(Path(__file__).parent.parent / "config" / ".env")


class ThreadsDirect:
    def __init__(self):
        self.user_id = _env.get("THREADS_USER_ID")
        self.token = _env.get("THREADS_ACCESS_TOKEN")
        self.base = "https://graph.threads.net/v1.0"

    def test_connection(self) -> bool:
        r = requests.get(
            f"{self.base}/me",
            params={"fields": "id,username", "access_token": self.token}
        )
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Threads 연결 성공!")
            print(f"   계정: @{data.get('username')}")
            print(f"   ID: {data.get('id')}")
            return True
        print(f"❌ 연결 실패: {r.json()}")
        return False

    def _split_text(self, text: str, limit: int = 490) -> list:
        if len(text) <= limit:
            return [text]
        parts, sections = [], [s.strip() for s in text.split("---") if s.strip()]
        current = ""
        for section in sections:
            cand = (current + "\n\n" + section).strip()
            if len(cand) <= limit:
                current = cand
            else:
                if current:
                    parts.append(current.strip())
                if len(section) > limit:
                    sub = ""
                    for line in section.split("\n"):
                        if len((sub + "\n" + line).strip()) <= limit:
                            sub = (sub + "\n" + line).strip()
                        else:
                            if sub: parts.append(sub)
                            sub = line
                    if sub: current = sub
                else:
                    current = section
        if current:
            parts.append(current.strip())
        return parts if parts else [text[:limit]]

    def _create_container(self, params: dict) -> str:
        params["access_token"] = self.token
        r = requests.post(f"{self.base}/{self.user_id}/threads", params=params, timeout=30)
        data = r.json()
        if "id" not in data:
            raise Exception(f"컨테이너 생성 실패: {data}")
        return data["id"]

    def _publish(self, creation_id: str) -> dict:
        time.sleep(2)  # API 처리 시간 필요
        r = requests.post(
            f"{self.base}/{self.user_id}/threads_publish",
            params={"creation_id": creation_id, "access_token": self.token},
            timeout=30
        )
        return r.json()

    def post_text(self, text: str) -> dict:
        if len(text) > 490:
            print(f"📏 {len(text)}자 → 자동 분할...")
            parts = self._split_text(text)
            print(f"   총 {len(parts)}개로 분할됨")
            return self.post_thread_series(parts)

        print(f"📝 Threads 게시 중... ({len(text)}자)")
        cid = self._create_container({"media_type": "TEXT", "text": text})
        result = self._publish(cid)
        if "id" in result:
            print(f"✅ 게시 완료! ID: {result['id']}")
            print(f"   👉 https://www.threads.net/@aikingdo/post/{result['id']}")
        else:
            print(f"❌ 발행 실패: {result}")
        return result

    def post_thread_series(self, posts: list) -> list:
        print(f"🧵 Thread 시리즈 게시 중... ({len(posts)}개)")
        results = []
        reply_to_id = None
        for i, text in enumerate(posts):
            params = {"media_type": "TEXT", "text": text}
            if reply_to_id:
                params["reply_to_id"] = reply_to_id
            cid = self._create_container(params)
            result = self._publish(cid)
            if "id" not in result:
                print(f"❌ {i+1}/{len(posts)} 실패: {result}")
                break
            reply_to_id = result["id"]
            results.append(result)
            print(f"  [{i+1}/{len(posts)}] ✅")
            time.sleep(1)
        print(f"🎉 시리즈 완료!")
        return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    t = ThreadsDirect()
    t.test_connection()
