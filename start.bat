@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 amap-poi-aoi ...
start "amap-poi-aoi server" cmd /k "uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"
timeout /t 6 /nobreak >nul
start "" http://127.0.0.1:8000
echo 已在新窗口启动服务，浏览器已打开 http://127.0.0.1:8000
echo 关闭那个窗口或在其中按 Ctrl+C 即可停止服务。
pause
