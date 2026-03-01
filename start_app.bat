@echo off
title AI Gundem Dashboard
echo ============================================
echo   AI Gundem Dashboard Baslatiliyor...
echo ============================================
echo.

cd /d "%~dp0"

:: Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo https://python.org adresinden Python 3.11+ indirin
    echo Kurulumda "Add to PATH" secenegini isaretleyin!
    pause
    exit /b 1
)

:: Bagimliliklari kur (ilk seferde)
if not exist ".deps_installed" (
    echo Bagimliliklar kuruluyor...
    pip install -r requirements.txt
    echo. > .deps_installed
)

echo.
echo Dashboard baslatiliyor: http://localhost:8501
echo Kapatmak icin bu pencereyi kapatin.
echo.

streamlit run 🏠_Ana_Sayfa.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
