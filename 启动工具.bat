@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 启动中...
start "" /B python -m http.server 8080
ping 127.0.0.1 -n 3 >nul
start "" "http://localhost:8080"
