@echo off
set "PATH=%PATH%;C:\Users\Administrator\.git-bin\cmd"
cd /d "%~dp0"
echo ========================================================
echo   Push WeChat-Silent-Agent to GitHub
echo ========================================================
echo.
echo Please create an empty repository on GitHub first:
echo https://github.com/new
echo.
set /p REPO_URL="Enter your GitHub repository URL (e.g. https://github.com/YourUsername/wechat-silent-agent.git): "
if "%REPO_URL%"=="" goto end

git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main
echo.
echo Pushing to GitHub...
git push -u origin main

:end
pause
