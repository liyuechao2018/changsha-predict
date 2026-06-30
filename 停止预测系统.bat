@echo off
chcp 65001 >nul
echo 正在停止长沙中考录取预测系统...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo 已尝试停止。
pause
