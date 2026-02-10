@echo off
echo ==========================================
echo      Spellcasters API Verification
echo ==========================================

echo [1/2] Running Test Suite (Pytest)...
python -m pytest
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Tests Failed!
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Building API...
python scripts/build_api.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build Failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ==========================================
echo      SUCCESS: Project is Valid!
echo ==========================================
exit /b 0
