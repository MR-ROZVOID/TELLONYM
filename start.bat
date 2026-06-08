@echo off
title Tellonym Bot Setup & Runner
color 0A

echo ==========================================
echo       Tellonym Bot - Auto Setup
echo ==========================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not installed or not in PATH.
    echo [*] Downloading Python 3.11...
    curl -o python-installer.exe https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe
    
    echo [*] Installing Python (This may take a minute)...
    start /wait python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    
    echo [+] Python installation finished. Cleaning up...
    del python-installer.exe
    
    echo [!] IMPORTANT: The terminal needs to reload the PATH variable.
    echo [!] Please CLOSE this window, then double-click this BAT file again to continue.
    pause
    exit /b
)

echo [+] Python is ready!
echo.

:: 2. Install required libraries
echo [*] Installing required Python libraries (selenium, requests)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install selenium requests

echo.
echo [+] All requirements are installed!
echo [*] Starting the bot...
echo ==========================================
echo.

:: 3. Run the script
python tellonym_register.py

echo.
pause
