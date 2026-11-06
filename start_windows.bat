@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.12 from python.org and enable Add Python to PATH.
  pause
  exit /b 1
)
echo Installing or updating Legal Counsel dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Please check your internet connection and Python version.
  pause
  exit /b 1
)
echo Starting the Legal Counsel Streamlit app locally...
python -m streamlit run streamlit_app.py
pause
endlocal
