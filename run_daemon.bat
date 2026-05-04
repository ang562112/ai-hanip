@echo off
chcp 65001 > nul
echo.
echo  AI한입 자동화 데몬 시작
echo  ========================
echo  매일 08:00 / 19:00 자동 게시
echo  종료: Ctrl+C
echo.
python3 "%~dp0src\scheduler.py" --daemon
pause
