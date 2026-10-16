@echo off
set "PATH=%PATH%;C:\Users\Administrator\.git-bin\cmd"
cd /d "%~dp0"
echo ========================================================
echo   Pushing WeChat-Silent-Agent to GitHub
echo   Target: https://github.com/quochoangzkqkz-boop/wechat-silent-agent.git
echo ========================================================
echo.
git remote remove origin 2>nul
git remote add origin https://github.com/quochoangzkqkz-boop/wechat-silent-agent.git
git branch -M main
echo Pushing to GitHub (If prompted, enter your GitHub Username and Personal Access Token)...
git push -u origin main
echo.
echo ========================================================
pause
