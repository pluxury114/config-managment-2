@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Error: virtual environment .venv was not found.
    exit /b 1
)
".venv\Scripts\python.exe" "src\main.py" %*
exit /b %ERRORLEVEL%
