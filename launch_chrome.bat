@echo off
echo Starting Google Chrome in Remote Debugging Mode on port 9222...
echo You can sign in to Naukri, LinkedIn, or Indeed in this window.
echo Once signed in, keep this window open and use Lazy-Jobber to automate applications.
echo.

set DEV_PROFILE=%USERPROFILE%\chrome-dev-profile
if not exist "%DEV_PROFILE%" mkdir "%DEV_PROFILE%"

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%DEV_PROFILE%" "https://www.naukri.com"
