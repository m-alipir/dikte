@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto failed
    .venv\Scripts\python.exe -m pip install PyQt6
    if errorlevel 1 goto failed
)
start "" .venv\Scripts\pythonw.exe mali.py --gui
exit /b
:failed
echo Kurulum tamamlanamadi. Python 3.11 veya daha yenisi gerekli.
pause
exit /b 1
