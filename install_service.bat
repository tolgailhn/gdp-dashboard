@echo off
REM Streamlit uygulamasini Windows Service olarak kurar
REM Gereksinim: NSSM (https://nssm.cc/download)
REM Kullanim: Yonetici olarak calistir (Sag tik > Run as Administrator)

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Bu scripti Yonetici olarak calistirin!
    echo Sag tik ^> Run as Administrator
    pause
    exit /b 1
)

set SERVICE_NAME=StreamlitApp
set APP_DIR=%~dp0
set APP_DIR=%APP_DIR:~0,-1%

REM NSSM kontrolu
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] NSSM bulunamadi!
    echo.
    echo Kurulum:
    echo   1. https://nssm.cc/download adresinden indir
    echo   2. nssm.exe'yi C:\Windows\ icine kopyala
    echo   veya: winget install NSSM
    echo.
    pause
    exit /b 1
)

echo ========================================
echo  Streamlit Windows Service Kurulumu
echo ========================================
echo  Dizin:  %APP_DIR%
echo  Service: %SERVICE_NAME%
echo.

REM Eski service varsa kaldir
nssm stop %SERVICE_NAME% >nul 2>&1
nssm remove %SERVICE_NAME% confirm >nul 2>&1

REM Yeni service olustur
nssm install %SERVICE_NAME% "%APP_DIR%\run.bat"
nssm set %SERVICE_NAME% AppDirectory "%APP_DIR%"
nssm set %SERVICE_NAME% DisplayName "X AI Otomasyon Dashboard"
nssm set %SERVICE_NAME% Description "Streamlit dashboard - otomatik baslatma ve crash recovery"

REM Otomatik yeniden baslatma (crash sonrasi 5sn bekle)
nssm set %SERVICE_NAME% AppExit Default Restart
nssm set %SERVICE_NAME% AppRestartDelay 5000

REM Otomatik baslatma (bilgisayar acilinca)
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Log dosyalari
nssm set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service.log"
nssm set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\error.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 5242880

REM logs dizini olustur
if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"

REM Servisi baslat
nssm start %SERVICE_NAME%

echo.
echo [OK] Kurulum tamamlandi!
echo.
echo Yararli komutlar:
echo   nssm status %SERVICE_NAME%          - Durum
echo   nssm restart %SERVICE_NAME%         - Yeniden baslat
echo   nssm stop %SERVICE_NAME%            - Durdur
echo   nssm edit %SERVICE_NAME%            - Ayarlar (GUI)
echo.
echo Log dosyalari:
echo   %APP_DIR%\logs\service.log
echo   %APP_DIR%\logs\error.log
echo.

nssm status %SERVICE_NAME%
pause
