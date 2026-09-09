@echo off
echo ===================================================
echo   Cleaning up lingering / zombie Python processes
echo ===================================================

powershell -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo Done! Starting Lazy-Jobber server cleanly...
.\venv\Scripts\python.exe server.py
