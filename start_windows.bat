@echo off
setlocal enabledelayedexpansion

REM ============================================
REM   DISCORD GUILD MANAGER - WINDOWS LAUNCHER
REM ============================================

echo.
echo ============================================
echo    DISCORD GUILD MANAGER
echo ============================================
echo.

REM --- CHECK PYTHON ---
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ======================================
    echo    ERROR: Python not found!
    echo ======================================
    echo.
    echo Python 3.8+ is required to run this script.
    echo.
    echo Download Python from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
echo       Python %PYTHON_VERSION% found

REM --- CHECK/CREATE VIRTUAL ENVIRONMENT ---
echo [2/4] Checking virtual environment...
if not exist "venv" (
    echo       Virtual environment not found
    echo       Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo       ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully
) else (
    echo       Virtual environment found
)

REM --- ACTIVATE VIRTUAL ENVIRONMENT ---
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo       ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

REM --- CHECK/INSTALL DEPENDENCIES ---
echo [4/4] Checking dependencies...

REM Check if .installed marker exists
if exist ".installed" (
    REM Check if requirements.txt was modified
    set REINSTALL=0
    
    REM Get current requirements hash
    for /f %%H in ('certutil -hashfile requirements.txt MD5 ^| find /v ":" ') do set CURRENT_HASH=%%H
    
    REM Get stored hash
    if exist ".installed" (
        for /f "tokens=*" %%A in (.installed) do set STORED_HASH=%%A
    )
    
    REM Compare hashes
    if not "!CURRENT_HASH!"=="!STORED_HASH!" (
        echo       Requirements changed, reinstalling dependencies...
        set REINSTALL=1
    ) else (
        echo       Dependencies already installed
    )
) else (
    echo       First run detected, installing dependencies...
    set REINSTALL=1
)

REM Install dependencies if needed
if "!REINSTALL!"=="1" (
    echo       Installing dependencies...
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo       ERROR: Failed to install dependencies!
        echo       Try running: pip install -r requirements.txt
        pause
        exit /b 1
    )
    
    REM Save requirements hash
    for /f %%H in ('certutil -hashfile requirements.txt MD5 ^| find /v ":" ') do echo %%H > .installed
    
    echo       Dependencies installed successfully
)

echo.
echo ============================================
echo    STARTING DISCORD GUILD MANAGER
echo ============================================
echo.

REM --- RUN MAIN SCRIPT ---
python main.py

REM --- COMPLETION ---
echo.
echo ============================================
echo    Script completed
echo    Press any key to exit...
echo ============================================
pause >nul