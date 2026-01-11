@echo off
chcp 65001 >nul
echo.
echo Claude Auto Fix Hook - Windows Installer
echo.
python "%~dp0install.py"
echo.
pause
