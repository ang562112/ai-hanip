"""
작업 스케줄러용 래퍼 — 콘솔 없는 환경 완전 대응
"""
import sys
import os
import datetime

# 경로 고정
BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src")
LOG  = os.path.join(BASE, "prompts", "run_log.txt")

os.makedirs(os.path.join(BASE, "prompts"), exist_ok=True)

# 모든 출력을 로그 파일로 리디렉션 (콘솔 없는 스케줄러 환경 대응)
log_file = open(LOG, "a", encoding="utf-8", buffering=1)
sys.stdout = log_file
sys.stderr = log_file

sys.path.insert(0, SRC)
os.chdir(SRC)

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

slot = int(sys.argv[1]) if len(sys.argv) > 1 else 0
log(f"=== 슬롯 {slot} 실행 시작 ===")

try:
    from scheduler import run_slot
    run_slot(slot)
    log("=== 완료 ===")
except Exception as e:
    log(f"=== 오류: {e} ===")
    import traceback
    traceback.print_exc()
finally:
    log_file.flush()
    log_file.close()
