@echo off
chcp 65001 >nul
echo.
echo Claude Auto Fix Hook - Windows Uninstaller
echo.
python "%~dp0uninstall.py"
echo.
pause
