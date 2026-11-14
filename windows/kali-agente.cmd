@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0kali-agente.ps1" %*
exit /b %ERRORLEVEL%
