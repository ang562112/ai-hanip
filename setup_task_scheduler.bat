@echo off
chcp 65001 > nul
echo.
echo  Windows 작업 스케줄러 등록
echo  ===========================

set SCRIPT_PATH=%~dp0src\scheduler.py
set PYTHON_PATH=python3

:: 오전 8시 — 슬롯 0
schtasks /create /tn "AI한입_오전게시" /tr "%PYTHON_PATH% \"%SCRIPT_PATH%\" --slot 0" /sc daily /st 08:00 /f
echo [완료] 오전 8시 자동 게시 등록

:: 저녁 7시 — 슬롯 1
schtasks /create /tn "AI한입_저녁게시" /tr "%PYTHON_PATH% \"%SCRIPT_PATH%\" --slot 1" /sc daily /st 19:00 /f
echo [완료] 저녁 7시 자동 게시 등록

echo.
echo  등록된 작업 확인:
schtasks /query /tn "AI한입_오전게시" /fo list /v | findstr "작업 이름\|다음 실행"
schtasks /query /tn "AI한입_저녁게시" /fo list /v | findstr "작업 이름\|다음 실행"

echo.
echo  완료! 이제 매일 자동으로 Threads에 게시됩니다.
pause
