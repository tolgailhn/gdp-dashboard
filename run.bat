@echo off
REM Streamlit uygulamasini baslatan wrapper script (Windows)
REM NSSM service veya dogrudan calistirma icin

cd /d "%~dp0"

REM Virtual environment varsa aktifle
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

streamlit run streamlit_app.py --server.headless true --server.address 0.0.0.0 --server.port 8502
