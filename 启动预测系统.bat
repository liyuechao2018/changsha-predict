@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo 未找到 Python 3。
        echo 请先安装 Python，并勾选 Add python.exe to PATH。
        echo 下载地址：https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
)

echo 正在启动长沙中考录取预测系统...
start "长沙中考录取预测系统" /min %PYTHON_CMD% app.py
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000"
echo 如果浏览器没有打开，请访问 http://127.0.0.1:8000
echo 服务已在后台窗口运行。关闭时请双击“停止预测系统.bat”。
pause
