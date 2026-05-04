@echo off
chcp 65001 > nul
echo.
echo  AI한입 — 오늘 콘텐츠 즉시 실행
echo.
python3 "%~dp0src\scheduler.py" --run
pause
