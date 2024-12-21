@echo off

:: Check if Python 3 is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python 3 could not be found. Please install it first.
    exit /b
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv .clif_lighthouse

:: Activate virtual environment
echo Activating virtual environment...
call .clif_lighthouse\Scripts\activate

:: Install requirements
echo Installing dependencies...
pip install -r requirements.txt

