@echo off
title WeChat-Silent-Agent Gateway
echo ========================================================
echo   Starting WeChat-Silent-Agent Gateway (DeepSeek-R1 8B)
echo ========================================================
cd /d "%~dp0"
python -m src.gateway
pause
