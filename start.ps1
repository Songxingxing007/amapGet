# 双击或右键运行：启动服务并打开浏览器
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
Start-Process -FilePath "cmd" -ArgumentList "/k", "uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"
Start-Sleep -Seconds 6
Start-Process "http://127.0.0.1:8000"
Write-Host "服务已启动：http://127.0.0.1:8000（关闭新窗口即停止）"
