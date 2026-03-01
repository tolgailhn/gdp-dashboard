@echo off
title AI Gundem Zamanlayici
echo ============================================
echo   AI Gundem Zamanlayici Baslatiliyor...
echo   Her 60 dakikada bir tarama yapacak
echo   Telegram bildirimi gonderecek
echo ============================================
echo.

cd /d "%~dp0"

:: Surekli tarama (her 60 dakikada bir)
python scheduled_scanner.py --loop 60 --hours 6

pause
