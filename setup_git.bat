@echo off
set "PATH=%PATH%;C:\Users\Administrator\.git-bin\cmd"
cd /d "C:\Users\Administrator\.gemini\antigravity\scratch\wechat-silent-agent"

git init
git config user.name "Developer"
git config user.email "developer@example.com"
git add .
git status
git commit -m "feat: Initial release of WeChat-Silent-Agent for WeChat 4.x"
git log -n 1
