@echo off
REM TikTok Video Generator - Windows Launcher
REM This script runs the generator from the current directory

REM Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo Error: Python not found in PATH.
        echo Please install Python 3.10+ and ensure "python" or "python3" is in PATH.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Check Python version
for /f "tokens=2 delims=. " %%a in ('%PYTHON_CMD% -c "import sys; print(sys.version_info[0], sys.version_info[1])"') do set PY_MINOR=%%a
if %PY_MINOR% lss 10 (
    echo Warning: Python 3.10+ recommended. Current version may work but is not officially supported.
)

REM Run the generator
echo Starting TikTok Video Generator...
echo.
%PYTHON_CMD% main.py
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo.
    echo Program exited with code %EXIT_CODE%.
)

exit /b %EXIT_CODE%