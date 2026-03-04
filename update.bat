@echo off
title AI Gundem - Guncelleme
echo ============================================
echo   Proje Guncelleniyor...
echo ============================================
echo.

cd /d "%~dp0"

:: Guncellemeleri cek
echo GitHub'dan son degisiklikler aliniyor...
git pull origin main

:: Yeni bagimlilik varsa kur
echo.
echo Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt --quiet

echo.
echo ============================================
echo   Guncelleme tamamlandi!
echo   Simdi start_app.bat ile uygulamayi baslatin.
echo ============================================
pause
