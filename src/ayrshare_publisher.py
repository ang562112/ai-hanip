"""
AI한입 — Ayrshare Threads 게시 모듈
(Meta 개발자 콘솔 없이 Threads 자동 게시)
"""

import requests
import json
import time
from pathlib import Path
from dotenv import dotenv_values

_env = dotenv_values(Path(__file__).parent.parent / "config" / ".env")

class AyrsharePublisher:
    def __init__(self):
        self.api_key = _env.get("AYRSHARE_API_KEY")
        self.base_url = "https://app.ayrshare.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> bool:
        resp = requests.get(f"{self.base_url}/user", headers=self.headers)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Ayrshare 연결 성공!")
            print(f"   연결된 플랫폼: {data.get('activeSocialAccounts', [])}")
            return True
        else:
            print(f"❌ 연결 실패: {resp.status_code}")
            return False

    def _request_with_retry(self, payload: dict, max_retries: int = 3) -> dict:
        """재시도 로직 (1초 → 3초 → 9초 백오프)"""
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/post",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                if not resp.text.strip():
                    raise Exception(f"빈 응답 (status {resp.status_code})")
                if resp.status_code >= 500:
                    raise Exception(f"서버 오류 {resp.status_code}")
                return resp.json()
            except Exception as e:
                wait = 3 ** attempt  # 1, 3, 9초
                if attempt < max_retries - 1:
                    print(f"⚠️  시도 {attempt+1} 실패 ({e}) → {wait}초 후 재시도...")
                    time.sleep(wait)
                else:
                    print(f"❌ {max_retries}회 모두 실패: {e}")
                    raise

    def _split_text(self, text: str, limit: int = 490) -> list:
        if len(text) <= limit:
            return [text]

        parts = []
        sections = [s.strip() for s in text.split("---") if s.strip()]
        current = ""

        for section in sections:
            candidate = (current + "\n\n" + section).strip()
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    parts.append(current.strip())
                if len(section) > limit:
                    lines = section.split("\n")
                    sub = ""
                    for line in lines:
                        if len((sub + "\n" + line).strip()) <= limit:
                            sub = (sub + "\n" + line).strip()
                        else:
                            if sub:
                                parts.append(sub)
                            sub = line
                    if sub:
                        current = sub
                else:
                    current = section

        if current:
            parts.append(current.strip())

        return parts if parts else [text[:limit]]

    def post_text(self, text: str) -> dict:
        if len(text) > 490:
            print(f"📏 {len(text)}자 → 자동 분할...")
            parts = self._split_text(text)
            print(f"   총 {len(parts)}개로 분할됨")
            return self.post_thread_series(parts)

        print(f"📝 Threads 게시 중... ({len(text)}자)")
        data = self._request_with_retry({"post": text, "platforms": ["threads"]})
        print(f"✅ 게시 완료!")
        post_ids = data.get('postIds', [])
        if post_ids:
            url = post_ids[0].get('postUrl', '')
            if url:
                print(f"   👉 {url}")
        return data

    def post_thread_series(self, posts: list) -> dict:
        print(f"🧵 Thread 시리즈 게시 중... ({len(posts)}개)")
        data = self._request_with_retry({
            "post": posts[0],
            "platforms": ["threads"],
            "threadPost": posts[1:]
        })
        print(f"✅ 시리즈 게시 완료!")
        return data

    def schedule_post(self, text: str, schedule_date: str) -> dict:
        print(f"⏰ 예약 게시 설정 중... ({schedule_date})")
        data = self._request_with_retry({
            "post": text,
            "platforms": ["threads"],
            "scheduleDate": schedule_date
        })
        print(f"✅ 예약 완료!")
        return data


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    pub = AyrsharePublisher()
    pub.test_connection()
